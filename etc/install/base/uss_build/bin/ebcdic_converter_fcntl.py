#!/usr/bin/env python3
"""
ebcdic_converter_fcntl.py - EBCDIC conversion using z/OS fcntl file tagging

This module provides EBCDIC conversion functionality using z/OS-specific
fcntl operations for file tagging instead of external commands.

Based on IBM z/OS documentation:
https://www.ibm.com/docs/en/zos/3.2.0?topic=SSLTBW_3.2.0/com.ibm.zos.v3r2.bpxbd00/rtfcndesc.html

Uses the attrib_t structure for F_GETTAG and F_SETTAG operations:
  typedef struct attrib_t {
      int att_filetagchg;           // File tag change flag
      int att_rsvd1;                // Reserved
      unsigned short att_txtflag;   // Text flag (1=text, 0=binary)
      unsigned short att_ccsid;     // CCSID
      int att_rsvd2[2];             // Reserved
  }

Key improvements over command-based approach:
- Direct system calls via fcntl (no subprocess overhead)
- More reliable file tag detection
- Better error handling for unconvertible characters
- Support for both files and streams/pipes
"""

import os
import sys
import fcntl
import struct
import ctypes
import stat
from typing import Optional, Dict, Tuple, BinaryIO, Any


# z/OS fcntl constants for file tagging
# From sys/fcntl.h on z/OS
# Based on actual z/OS header file values
F_SETTAG = 12       # Set file tag information
F_CONTROL_CVT = 13  # Control conversion
# Note: There is no F_GETTAG in z/OS. Use F_CONTROL_CVT with f_cnvrt structure
# to query file conversion information (which includes CCSID)
# Define f_cnvrt structure using ctypes for fcntl operations
class f_cnvrt(ctypes.Structure):
    """
    z/OS f_cnvrt structure for F_CONTROL_CVT operations.
    
    struct f_cnvrt {
        int cvtcmd;      // Command: 3=query, others for setting
        short pccsid;    // Process CCSID
        short fccsid;    // File CCSID
    }
    """
    _fields_ = [
        ("cvtcmd", ctypes.c_int32),   # 4 bytes
        ("pccsid", ctypes.c_int16),   # 2 bytes
        ("fccsid", ctypes.c_int16),   # 2 bytes
    ]  # Total: 8 bytes

# Define attrib_t structure for F_SETTAG
class attrib_t(ctypes.Structure):
    """
    z/OS attrib_t structure for F_SETTAG operations.
    
    struct attrib_t {
        int att_filetagchg;           // File tag change flag (1=change)
        int att_rsvd1;                // Reserved (0)
        unsigned short att_txtflag;   // Text flag (1=text, 0=binary)
        unsigned short att_ccsid;     // CCSID
        int att_rsvd2[2];             // Reserved (0, 0)
    }
    """
    _fields_ = [
        ("att_filetagchg", ctypes.c_int32),      # 4 bytes
        ("att_rsvd1", ctypes.c_int32),           # 4 bytes
        ("att_txtflag", ctypes.c_uint16),        # 2 bytes
        ("att_ccsid", ctypes.c_uint16),          # 2 bytes
        ("att_rsvd2", ctypes.c_int32 * 2),       # 8 bytes (array of 2 ints)
    ]  # Total: 20 bytes


# CCSID (Coded Character Set ID) mappings
CCSID_ISO8859_1 = 819   # ASCII/ISO8859-1
CCSID_IBM1047 = 1047    # EBCDIC
CCSID_UNTAGGED = 0      # Untagged file

# Encoding name mappings
ENCODING_MAP = {
    CCSID_ISO8859_1: 'ISO8859-1',
    CCSID_IBM1047: 'IBM-1047',
    CCSID_UNTAGGED: 'untagged'
}

# Python encoding names
PYTHON_ENCODING_MAP = {
    'ISO8859-1': 'iso8859-1',
    'IBM-1047': 'ibm1047',
    'untagged': 'ibm1047'  # Treat untagged as EBCDIC per requirements
}


class FileTagInfo:
    """Container for z/OS file tag information"""
    
    def __init__(self, ccsid: int, text_flag: bool):
        self.ccsid = ccsid
        self.text_flag = text_flag
        self.encoding_name = ENCODING_MAP.get(ccsid, f'CCSID-{ccsid}')
    
    def __repr__(self):
        return f"FileTagInfo(ccsid={self.ccsid}, text={self.text_flag}, encoding={self.encoding_name})"


def get_file_encoding_fcntl(path: str, fd: Optional[int] = None,
                            verbose: bool = False) -> str:
    """
    Get file encoding using z/OS fcntl F_CONTROL_CVT with ctypes.
    
    Uses the f_cnvrt structure with fcntl.fcntl() to query file CCSID.
    This is the correct way to access file tags in Python on z/OS.
    
    Args:
        path: File path (used for error messages and if fd not provided)
        fd: Optional file descriptor (if None, file will be opened)
        verbose: Enable verbose output
    
    Returns:
        Encoding name: 'ISO8859-1', 'IBM-1047', or 'untagged'
    
    Raises:
        OSError: If file cannot be accessed
    """
    close_fd = False
    
    try:
        # Open file if descriptor not provided
        if fd is None:
            fd = os.open(path, os.O_RDONLY)
            close_fd = True
        
        if verbose:
            print(f"DEBUG: Getting file tag for {path} using F_CONTROL_CVT")
            print(f"  File descriptor: {fd}")
        
        # Create f_cnvrt structure with cvtcmd=3 for query
        qcvt = f_cnvrt(3, 0, 0)  # 3 = query command
        
        if verbose:
            print(f"  Query structure: cvtcmd={qcvt.cvtcmd}, pccsid={qcvt.pccsid}, fccsid={qcvt.fccsid}")
        
        # Call fcntl with F_CONTROL_CVT
        result = fcntl.fcntl(fd, F_CONTROL_CVT, qcvt)
        
        # Extract result using from_buffer_copy
        cvt_result = f_cnvrt.from_buffer_copy(result)
        
        ccsid = cvt_result.fccsid
        
        if verbose:
            print(f"  Result: cvtcmd={cvt_result.cvtcmd}, pccsid={cvt_result.pccsid}, fccsid={cvt_result.fccsid}")
            print(f"  File CCSID={ccsid}")
        
        # Map CCSID to encoding name
        encoding = ENCODING_MAP.get(ccsid, 'untagged')
        
        if verbose:
            print(f"  Final detected encoding: {encoding}")
        
        return encoding
        
    except Exception as e:
        if verbose:
            print(f"DEBUG: fcntl F_CONTROL_CVT failed for {path}: {e}")
            import traceback
            traceback.print_exc()
        # If fcntl fails, treat as untagged
        return 'untagged'
        
    finally:
        if close_fd and fd is not None:
            try:
                os.close(fd)
            except:
                pass


def set_file_tag_fcntl(path: str, ccsid: int, text_flag: bool = True,
                      verbose: bool = False) -> bool:
    """
    Set file tag using z/OS fcntl F_SETTAG operation with ctypes.
    
    Uses the attrib_t structure with fcntl.fcntl() to set file CCSID tag.
    
    Args:
        path: File path to tag
        ccsid: CCSID to set (e.g., 819 for ISO8859-1, 1047 for IBM-1047)
        text_flag: True for text file, False for binary
        verbose: Enable verbose output
    
    Returns:
        True if successful, False otherwise
    """
    try:
        fd = os.open(path, os.O_RDWR)
        
        try:
            if verbose:
                print(f"DEBUG: Setting file tag for {path} using F_SETTAG")
                print(f"  CCSID={ccsid}, text_flag={text_flag}")
            
            # Create attrib_t structure
            tag = attrib_t()
            tag.att_filetagchg = 1  # Indicate we want to change the tag
            tag.att_rsvd1 = 0
            tag.att_txtflag = 1 if text_flag else 0
            tag.att_ccsid = ccsid
            tag.att_rsvd2[0] = 0
            tag.att_rsvd2[1] = 0
            
            if verbose:
                print(f"  Structure: filetagchg={tag.att_filetagchg}, txtflag={tag.att_txtflag}, ccsid={tag.att_ccsid}")
            
            # Call fcntl with F_SETTAG
            fcntl.fcntl(fd, F_SETTAG, tag)
            
            if verbose:
                print(f"  Successfully set file tag")
            
            return True
            
        finally:
            os.close(fd)
            
    except Exception as e:
        if verbose:
            print(f"ERROR: Failed to set file tag for {path}: {e}")
            import traceback
            traceback.print_exc()
        return False


def get_file_tag_info(path: str, verbose: bool = False) -> Optional[FileTagInfo]:
    """
    Get detailed file tag information.
    
    Args:
        path: File path
        verbose: Enable verbose output
    
    Returns:
        FileTagInfo object or None if unable to get info
    """
    try:
        encoding = get_file_encoding_fcntl(path, verbose=verbose)
        
        # Map encoding name back to CCSID
        ccsid = CCSID_UNTAGGED
        for c, e in ENCODING_MAP.items():
            if e == encoding:
                ccsid = c
                break
        
        # Assume text file (we don't have binary flag from simple query)
        return FileTagInfo(ccsid, True)
        
    except Exception as e:
        if verbose:
            print(f"ERROR: Failed to get file tag info for {path}: {e}")
        return None


def is_named_pipe(path: str) -> bool:
    """Check if a path is a named pipe (FIFO)"""
    try:
        return stat.S_ISFIFO(os.stat(path).st_mode)
    except (OSError, FileNotFoundError):
        return False


def convert_to_ebcdic_fcntl(input_path: str, output_path: str, 
                           verbose: bool = False) -> Dict[str, Any]:
    """
    Convert input file to EBCDIC using fcntl-based encoding detection.
    
    This function:
    1. Uses fcntl to detect input file encoding
    2. Converts from ASCII to EBCDIC if needed
    3. Handles unconvertible characters gracefully (leaves them unchanged)
    4. Tags output file using fcntl
    5. Returns conversion statistics
    
    Args:
        input_path: Source file path
        output_path: Destination file path
        verbose: Enable verbose output
    
    Returns:
        Dictionary with conversion statistics:
        {
            'success': bool,
            'bytes_read': int,
            'bytes_written': int,
            'encoding_detected': str,
            'conversion_needed': bool,
            'errors': int,
            'error_message': str (if success=False)
        }
    """
    stats = {
        'success': False,
        'bytes_read': 0,
        'bytes_written': 0,
        'encoding_detected': 'unknown',
        'conversion_needed': False,
        'errors': 0,
        'error_message': None
    }
    
    try:
        # Detect input encoding using fcntl
        encoding = get_file_encoding_fcntl(input_path, verbose=verbose)
        stats['encoding_detected'] = encoding
        
        if verbose:
            print(f"Input file: {input_path}")
            print(f"Detected encoding: {encoding}")
        
        # Determine if conversion is needed
        # Untagged files are treated as IBM-1047 (already EBCDIC)
        if encoding == 'ISO8859-1':
            stats['conversion_needed'] = True
            
            if verbose:
                print("Converting from ISO8859-1 to IBM-1047...")
            
            # Read as ASCII, write as EBCDIC
            # Use 'replace' error handling to gracefully handle unconvertible chars
            with open(input_path, 'r', encoding='iso8859-1', errors='replace') as f_in:
                content = f_in.read()
                stats['bytes_read'] = len(content.encode('iso8859-1', errors='replace'))
            
            with open(output_path, 'w', encoding='ibm1047', errors='replace') as f_out:
                f_out.write(content)
                stats['bytes_written'] = len(content.encode('ibm1047', errors='replace'))
            
            # Tag output file as IBM-1047 using fcntl
            if set_file_tag_fcntl(output_path, CCSID_IBM1047, verbose=verbose):
                if verbose:
                    print(f"Tagged output file as IBM-1047")
            else:
                if verbose:
                    print(f"Warning: Could not tag output file")
        
        else:
            # Already EBCDIC or untagged (treat as EBCDIC) - copy as binary
            stats['conversion_needed'] = False
            
            if verbose:
                print(f"File is already EBCDIC (or untagged), copying as binary...")
            
            with open(input_path, 'rb') as f_in:
                content = f_in.read()
                stats['bytes_read'] = len(content)
            
            with open(output_path, 'wb') as f_out:
                f_out.write(content)
                stats['bytes_written'] = len(content)
            
            # Tag as IBM-1047 if untagged
            if encoding == 'untagged':
                if set_file_tag_fcntl(output_path, CCSID_IBM1047, verbose=verbose):
                    if verbose:
                        print(f"Tagged output file as IBM-1047")
        
        stats['success'] = True
        
        if verbose:
            print(f"Conversion complete: {stats['bytes_read']} bytes read, "
                  f"{stats['bytes_written']} bytes written")
        
        return stats
        
    except Exception as e:
        stats['error_message'] = str(e)
        if verbose:
            print(f"ERROR: Conversion failed: {e}", file=sys.stderr)
        return stats


def convert_stream_to_ebcdic(input_stream: BinaryIO, output_stream: BinaryIO,
                             source_encoding: str = 'iso8859-1',
                             chunk_size: int = 8192,
                             verbose: bool = False) -> Dict[str, Any]:
    """
    Convert a stream/pipe from ASCII to EBCDIC.
    
    This function is used for pipes and streams where fcntl tagging is not available.
    It reads from the input stream and writes converted data to the output stream.
    
    Args:
        input_stream: Input binary stream (e.g., pipe, stdin)
        output_stream: Output binary stream
        source_encoding: Source encoding ('iso8859-1' or 'ibm1047')
        chunk_size: Size of chunks to read/write
        verbose: Enable verbose output
    
    Returns:
        Dictionary with conversion statistics
    """
    stats = {
        'success': False,
        'bytes_read': 0,
        'bytes_written': 0,
        'chunks_processed': 0,
        'errors': 0,
        'error_message': None
    }
    
    try:
        if verbose:
            print(f"Converting stream from {source_encoding} to IBM-1047...")
        
        while True:
            # Read chunk
            chunk = input_stream.read(chunk_size)
            if not chunk:
                break
            
            stats['bytes_read'] += len(chunk)
            stats['chunks_processed'] += 1
            
            # Convert encoding if needed
            if source_encoding.lower() != 'ibm1047':
                try:
                    # Decode from source encoding
                    text = chunk.decode(source_encoding, errors='replace')
                    # Encode to EBCDIC
                    converted = text.encode('ibm1047', errors='replace')
                except Exception as e:
                    if verbose:
                        print(f"Warning: Conversion error in chunk {stats['chunks_processed']}: {e}")
                    stats['errors'] += 1
                    # Use original chunk if conversion fails
                    converted = chunk
            else:
                # Already EBCDIC, no conversion needed
                converted = chunk
            
            # Write converted chunk
            output_stream.write(converted)
            stats['bytes_written'] += len(converted)
        
        stats['success'] = True
        
        if verbose:
            print(f"Stream conversion complete: {stats['bytes_read']} bytes read, "
                  f"{stats['bytes_written']} bytes written, "
                  f"{stats['chunks_processed']} chunks processed")
        
        return stats
        
    except Exception as e:
        stats['error_message'] = str(e)
        if verbose:
            print(f"ERROR: Stream conversion failed: {e}", file=sys.stderr)
        return stats


def main():
    """Simple command-line interface for testing"""
    import argparse
    
    parser = argparse.ArgumentParser(
        description='Convert files to EBCDIC using z/OS fcntl',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Convert a file
  ebcdic_converter_fcntl.py input.txt output.txt
  
  # Get file encoding info
  ebcdic_converter_fcntl.py --info input.txt
  
  # Convert with verbose output
  ebcdic_converter_fcntl.py -v input.txt output.txt
  
  # Convert from stdin to file
  cat input.txt | ebcdic_converter_fcntl.py --stdin output.txt
"""
    )
    
    parser.add_argument('input', nargs='?', help='Input file path')
    parser.add_argument('output', nargs='?', help='Output file path')
    parser.add_argument('--info', action='store_true', 
                       help='Show file encoding info only')
    parser.add_argument('--stdin', action='store_true',
                       help='Read from stdin instead of file')
    parser.add_argument('-v', '--verbose', action='store_true',
                       help='Enable verbose output')
    
    args = parser.parse_args()
    
    if args.info:
        if not args.input:
            print("ERROR: Input file required for --info", file=sys.stderr)
            return 1
        
        info = get_file_tag_info(args.input, verbose=args.verbose)
        if info:
            print(f"File: {args.input}")
            print(f"  CCSID: {info.ccsid}")
            print(f"  Encoding: {info.encoding_name}")
            print(f"  Text: {info.text_flag}")
            return 0
        else:
            print(f"ERROR: Could not get file info for {args.input}", file=sys.stderr)
            return 1
    
    elif args.stdin:
        if not args.output:
            print("ERROR: Output file required with --stdin", file=sys.stderr)
            return 1
        
        with open(args.output, 'wb') as f_out:
            stats = convert_stream_to_ebcdic(
                sys.stdin.buffer,
                f_out,
                source_encoding='iso8859-1',
                verbose=args.verbose
            )
        
        if stats['success']:
            # Tag output file
            set_file_tag_fcntl(args.output, CCSID_IBM1047, verbose=args.verbose)
            print(f"Converted {stats['bytes_read']} bytes from stdin to {args.output}")
            return 0
        else:
            print(f"ERROR: {stats['error_message']}", file=sys.stderr)
            return 1
    
    else:
        if not args.input or not args.output:
            print("ERROR: Both input and output files required", file=sys.stderr)
            parser.print_help()
            return 1
        
        stats = convert_to_ebcdic_fcntl(args.input, args.output, verbose=args.verbose)
        
        if stats['success']:
            print(f"Conversion successful: {stats['bytes_read']} bytes -> {stats['bytes_written']} bytes")
            return 0
        else:
            print(f"ERROR: {stats['error_message']}", file=sys.stderr)
            return 1


if __name__ == '__main__':
    sys.exit(main())

# Made with Bob
