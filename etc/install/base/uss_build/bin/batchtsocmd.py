#!/usr/bin/env python3
"""
tester.py - Execute TSO commands via IKJEFT1B with encoding conversion
Handles SYSIN and SYSTSIN inputs (files or pipes) with ASCII/EBCDIC conversion
"""

import sys
import os
import argparse
import stat
import tempfile
from zoautil_py import mvscmd
from zoautil_py.ztypes import DDStatement, FileDefinition, DatasetDefinition


def is_named_pipe(path: str) -> bool:
    """Check if a path is a named pipe (FIFO)"""
    try:
        return stat.S_ISFIFO(os.stat(path).st_mode)
    except (OSError, FileNotFoundError):
        return False


def get_file_encoding(path: str) -> str:
    """
    Get the encoding tag of a file.
    Returns 'IBM-1047' for EBCDIC, 'ISO8859-1' for ASCII, or 'untagged'
    """
    try:
        # Get file tag using os.stat_result
        stat_result = os.stat(path)
        # Check if file has a tag attribute
        if hasattr(stat_result, 'st_tag'):
            tag = stat_result.st_tag
            if tag.ccsid == 1047:
                return 'IBM-1047'
            elif tag.ccsid == 819:  # ISO8859-1
                return 'ISO8859-1'
        return 'untagged'
    except (OSError, AttributeError):
        return 'untagged'


def convert_to_ebcdic(input_path: str, output_path: str, verbose: bool = False) -> bool:
    """
    Convert input file from ASCII to EBCDIC if needed.
    If already EBCDIC or untagged (assumed EBCDIC), copy as-is.
    
    Args:
        input_path: Source file path
        output_path: Destination file path
        verbose: Enable verbose output
    
    Returns:
        True if successful, False otherwise
    """
    try:
        encoding = get_file_encoding(input_path)
        
        if verbose:
            print(f"Input encoding detected: {encoding}")
        
        if encoding == 'ISO8859-1':
            # Read as ASCII and write as EBCDIC
            with open(input_path, 'r', encoding='iso8859-1') as f_in:
                content = f_in.read()
            
            with open(output_path, 'w', encoding='ibm1047') as f_out:
                f_out.write(content)
            
            # Tag output file as IBM-1047
            os.system(f"chtag -tc IBM-1047 {output_path}")
            
            if verbose:
                print(f"Converted {input_path} from ASCII to EBCDIC")
        else:
            # Already EBCDIC or untagged (assume EBCDIC) - copy as binary
            with open(input_path, 'rb') as f_in:
                content = f_in.read()
            
            with open(output_path, 'wb') as f_out:
                f_out.write(content)
            
            # Tag as IBM-1047 if untagged
            if encoding == 'untagged':
                os.system(f"chtag -tc IBM-1047 {output_path}")
                if verbose:
                    print(f"Tagged {output_path} as IBM-1047")
        
        return True
        
    except Exception as e:
        print(f"ERROR: Failed to convert {input_path}: {e}", file=sys.stderr)
        return False


def validate_input_file(path: str, name: str) -> bool:
    """Validate that input file or named pipe exists and is readable"""
    if not os.path.exists(path):
        print(f"ERROR: {name} file does not exist: {path}", file=sys.stderr)
        return False
    
    if not os.access(path, os.R_OK):
        print(f"ERROR: {name} file is not readable: {path}", file=sys.stderr)
        return False
    
    return True


def execute_tso_command(systsin_file: str, sysin_file: str,
                       systsprt_file: str, sysprint_file: str,
                       steplib: str | None = None, verbose: bool = False) -> int:
    """
    Execute TSO command using IKJEFT1B with SYSTSIN and SYSIN inputs
    
    Args:
        systsin_file: Path to SYSTSIN input file or named pipe
        sysin_file: Path to SYSIN input file or named pipe
        systsprt_file: Path to SYSTSPRT output file or named pipe
        sysprint_file: Path to SYSPRINT output file or named pipe
        steplib: Optional STEPLIB dataset name
        verbose: Enable verbose output
    
    Returns:
        Return code from IKJEFT1B execution
    """
    
    # Validate input files
    if not validate_input_file(systsin_file, "SYSTSIN"):
        return 8
    
    if not validate_input_file(sysin_file, "SYSIN"):
        return 8
    
    # Check if inputs are named pipes
    systsin_is_pipe = is_named_pipe(systsin_file)
    sysin_is_pipe = is_named_pipe(sysin_file)
    
    if verbose:
        print(f"SYSTSIN: {systsin_file} {'(named pipe)' if systsin_is_pipe else '(file)'}")
        print(f"SYSIN: {sysin_file} {'(named pipe)' if sysin_is_pipe else '(file)'}")
    
    # Create temporary files for EBCDIC conversion
    temp_systsin = None
    temp_sysin = None
    
    try:
        # Convert SYSTSIN to EBCDIC
        temp_systsin = tempfile.NamedTemporaryFile(mode='wb', delete=False, suffix='.systsin')
        temp_systsin.close()
        
        if not convert_to_ebcdic(systsin_file, temp_systsin.name, verbose):
            return 8
        
        # Convert SYSIN to EBCDIC
        temp_sysin = tempfile.NamedTemporaryFile(mode='wb', delete=False, suffix='.sysin')
        temp_sysin.close()
        
        if not convert_to_ebcdic(sysin_file, temp_sysin.name, verbose):
            return 8
        
        # Define DD statements for IKJEFT1B
        dds = []
        
        # Add STEPLIB if specified
        if steplib:
            dds.append(DDStatement('STEPLIB', DatasetDefinition(steplib)))
            if verbose:
                print(f"STEPLIB: {steplib}")
        
        # Add remaining DD statements
        dds.extend([
            DDStatement('SYSTSPRT', FileDefinition(systsprt_file)),
            DDStatement('SYSTSIN', FileDefinition(temp_systsin.name)),
            DDStatement('SYSPRINT', FileDefinition(sysprint_file)),
            DDStatement('SYSUDUMP', FileDefinition('DUMMY')),
            DDStatement('SYSIN', FileDefinition(temp_sysin.name))
        ])
        
        if verbose:
            print("Executing IKJEFT1B via mvscmdauth...")
        
        # Execute IKJEFT1B using mvscmdauth
        response = mvscmd.execute_authorized(
            pgm='IKJEFT1B',
            dds=dds,
            verbose=verbose
        )
        
        if verbose or response.rc != 0:
            print(f"\nReturn code: {response.rc}")
        
        # Tag output files as IBM-1047
        if not is_named_pipe(systsprt_file):
            os.system(f"chtag -tc IBM-1047 {systsprt_file}")
            if verbose:
                print(f"Tagged {systsprt_file} as IBM-1047")
        
        if not is_named_pipe(sysprint_file):
            os.system(f"chtag -tc IBM-1047 {sysprint_file}")
            if verbose:
                print(f"Tagged {sysprint_file} as IBM-1047")
        
        return response.rc
        
    except Exception as e:
        print(f"ERROR: Failed to execute IKJEFT1B: {e}", file=sys.stderr)
        return 16
        
    finally:
        # Clean up temporary files
        if temp_systsin and os.path.exists(temp_systsin.name):
            os.unlink(temp_systsin.name)
        if temp_sysin and os.path.exists(temp_sysin.name):
            os.unlink(temp_sysin.name)


def main():
    """Main entry point"""
    parser = argparse.ArgumentParser(
        description='Execute TSO commands via IKJEFT1B with encoding conversion',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Using regular files
  batchtsocmd.py --systsin systsin.txt --sysin input.txt --systsprt output.txt --sysprint print.txt
  
  # Using named pipes
  mkfifo /tmp/systsin.pipe /tmp/sysin.pipe /tmp/systsprt.pipe /tmp/sysprint.pipe
  batchtsocmd.py --systsin /tmp/systsin.pipe --sysin /tmp/sysin.pipe \\
                 --systsprt /tmp/systsprt.pipe --sysprint /tmp/sysprint.pipe
  
  # With STEPLIB and verbose output
  batchtsocmd.py --systsin systsin.txt --sysin input.txt \\
                 --systsprt output.txt --sysprint print.txt \\
                 --steplib DB2V13.SDSNLOAD --verbose

Note: Input files can be ASCII (ISO8859-1) or EBCDIC (IBM-1047).
      Untagged files are assumed to be EBCDIC.
      Output files will be tagged as IBM-1047.
"""
    )
    
    parser.add_argument(
        '--systsin',
        required=True,
        help='Path to SYSTSIN input file or named pipe'
    )
    
    parser.add_argument(
        '--sysin',
        required=True,
        help='Path to SYSIN input file or named pipe'
    )
    
    parser.add_argument(
        '--systsprt',
        required=True,
        help='Path to SYSTSPRT output file or named pipe'
    )
    
    parser.add_argument(
        '--sysprint',
        required=True,
        help='Path to SYSPRINT output file or named pipe'
    )
    
    parser.add_argument(
        '--steplib',
        help='Optional STEPLIB dataset name (e.g., DB2V13.SDSNLOAD)'
    )
    
    parser.add_argument(
        '-v', '--verbose',
        action='store_true',
        help='Enable verbose output'
    )
    
    args = parser.parse_args()
    
    # Execute the TSO command
    rc = execute_tso_command(
        args.systsin,
        args.sysin,
        args.systsprt,
        args.sysprint,
        args.steplib,
        args.verbose
    )
    
    return rc


if __name__ == '__main__':
    sys.exit(main())

# Made with Bob
