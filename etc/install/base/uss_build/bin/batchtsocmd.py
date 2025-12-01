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


def get_file_encoding(path: str, verbose: bool = False) -> str:
    """
    Get the encoding tag of a file using ls -T command.
    Returns 'IBM-1047' for EBCDIC, 'ISO8859-1' for ASCII, or 'untagged'
    """
    try:
        # Use ls -T to get file tag information on z/OS
        import subprocess
        result = subprocess.run(['ls', '-T', path],
                              capture_output=True,
                              text=True,
                              encoding='iso8859-1')
        
        if result.returncode == 0:
            output = result.stdout.strip()
            if verbose:
                print(f"DEBUG: ls -T output for {path}: {output}")
            
            # Parse the output - format is like: "t ISO8859-1   T=on  -rw-r--r--..."
            parts = output.split()
            if len(parts) > 1:
                # First part is 't' or 'b' or '-' (text/binary/untagged)
                # Second part is the codeset name
                tag_type = parts[0]
                if tag_type == 't' and len(parts) > 1:
                    codeset = parts[1]
                    if verbose:
                        print(f"DEBUG: Detected codeset: {codeset}")
                    
                    if codeset == 'IBM-1047':
                        return 'IBM-1047'
                    elif codeset == 'ISO8859-1':
                        return 'ISO8859-1'
                    else:
                        if verbose:
                            print(f"DEBUG: Unknown codeset: {codeset}")
                        return 'untagged'
                elif tag_type == '-':
                    if verbose:
                        print(f"DEBUG: File is untagged")
                    return 'untagged'
        
        if verbose:
            print(f"DEBUG: Could not determine encoding from ls -T")
        return 'untagged'
        
    except Exception as e:
        if verbose:
            print(f"DEBUG: Exception in get_file_encoding for {path}: {e}")
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
        encoding = get_file_encoding(input_path, verbose)
        
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
                       systsprt_file: str | None = None,
                       sysprint_file: str | None = None,
                       steplib: str | None = None, verbose: bool = False) -> int:
    """
    Execute TSO command using IKJEFT1B with SYSTSIN and SYSIN inputs
    
    Args:
        systsin_file: Path to SYSTSIN input file or named pipe
        sysin_file: Path to SYSIN input file or named pipe
        systsprt_file: Optional path to SYSTSPRT output file or named pipe (defaults to DUMMY)
        sysprint_file: Optional path to SYSPRINT output file or named pipe (defaults to stdout)
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
    temp_sysprint = None
    
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
        
        # Add SYSTSPRT - use DUMMY if not specified
        if systsprt_file:
            dds.append(DDStatement('SYSTSPRT', FileDefinition(systsprt_file)))
        else:
            dds.append(DDStatement('SYSTSPRT', FileDefinition('DUMMY')))
            if verbose:
                print("SYSTSPRT: DUMMY")
        
        # Add SYSTSIN
        dds.append(DDStatement('SYSTSIN', FileDefinition(temp_systsin.name)))
        
        # Add SYSPRINT - use stdout if not specified, tagged as IBM-1047
        if sysprint_file:
            dds.append(DDStatement('SYSPRINT', FileDefinition(sysprint_file)))
        else:
            # Create a temporary file for stdout that will be tagged
            temp_sysprint = tempfile.NamedTemporaryFile(mode='wb', delete=False, suffix='.sysprint')
            temp_sysprint.close()
            os.system(f"chtag -tc IBM-1047 {temp_sysprint.name}")
            dds.append(DDStatement('SYSPRINT', FileDefinition(temp_sysprint.name)))
            if verbose:
                print("SYSPRINT: stdout (tagged as IBM-1047)")
        
        # Add remaining DD statements
        dds.extend([
            DDStatement('SYSUDUMP', FileDefinition('DUMMY')),
            DDStatement('SYSIN', FileDefinition(temp_sysin.name))
        ])
        
        if verbose:
            print("Executing IKJEFT1B via mvscmdauth...")
            print("\nDD Statements:")
            for dd in dds:
                print(f"  {dd.name}: {dd.definition}")
            print()
        
        # Execute IKJEFT1B using mvscmdauth
        response = mvscmd.execute_authorized(
            pgm='IKJEFT1B',
            dds=dds,
            verbose=verbose
        )
        
        # If SYSPRINT was sent to temp file (stdout), read and print it
        if not sysprint_file and temp_sysprint:
            try:
                with open(temp_sysprint.name, 'r', encoding='ibm1047') as f:
                    print(f.read())
            except Exception as e:
                if verbose:
                    print(f"Warning: Could not read SYSPRINT output: {e}", file=sys.stderr)
            finally:
                if os.path.exists(temp_sysprint.name):
                    os.unlink(temp_sysprint.name)
        
        if verbose or response.rc != 0:
            print(f"\nReturn code: {response.rc}")
        
        # Tag output files as IBM-1047
        if systsprt_file and not is_named_pipe(systsprt_file):
            os.system(f"chtag -tc IBM-1047 {systsprt_file}")
            if verbose:
                print(f"Tagged {systsprt_file} as IBM-1047")
        
        if sysprint_file and not is_named_pipe(sysprint_file):
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
  batchtsocmd.py --systsin systsin.txt --sysin input.txt
  
  # With output files
  batchtsocmd.py --systsin systsin.txt --sysin input.txt \\
                 --systsprt output.txt --sysprint print.txt
  
  # Using named pipes
  mkfifo /tmp/systsin.pipe /tmp/sysin.pipe /tmp/systsprt.pipe /tmp/sysprint.pipe
  batchtsocmd.py --systsin /tmp/systsin.pipe --sysin /tmp/sysin.pipe \\
                 --systsprt /tmp/systsprt.pipe --sysprint /tmp/sysprint.pipe
  
  # With STEPLIB and verbose output
  batchtsocmd.py --systsin systsin.txt --sysin input.txt \\
                 --steplib DB2V13.SDSNLOAD --verbose

Note: Input files can be ASCII (ISO8859-1) or EBCDIC (IBM-1047).
      Untagged files are assumed to be EBCDIC.
      Output files will be tagged as IBM-1047.
      If --systsprt is not specified, output goes to DUMMY.
      If --sysprint is not specified, output goes to stdout (tagged as IBM-1047).
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
        help='Path to SYSTSPRT output file or named pipe (defaults to DUMMY)'
    )
    
    parser.add_argument(
        '--sysprint',
        help='Path to SYSPRINT output file or named pipe (defaults to stdout, tagged as IBM-1047)'
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
