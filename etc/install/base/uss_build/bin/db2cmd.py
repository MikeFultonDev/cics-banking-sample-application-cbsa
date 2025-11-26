#!/usr/bin/env python3
"""
db2cmd - Execute DB2 commands via IKJEFT1B
Uses mvscmdauth to run IKJEFT1B with SYSTSIN and SYSIN inputs from files or named pipes
"""

import sys
import os
import argparse
import stat
from zoautil_py import mvscmd
from zoautil_py.ztypes import DDStatement, FileDefinition


def is_named_pipe(path: str) -> bool:
    """Check if a path is a named pipe (FIFO)"""
    try:
        return stat.S_ISFIFO(os.stat(path).st_mode)
    except (OSError, FileNotFoundError):
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


def execute_db2_command(systsin_file: str, sysin_file: str, verbose: bool = False) -> int:
    """
    Execute DB2 command using IKJEFT1B with SYSTSIN and SYSIN inputs
    
    Args:
        systsin_file: Path to SYSTSIN input file or named pipe
        sysin_file: Path to SYSIN input file or named pipe
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
    
    # Define DD statements for IKJEFT1B
    dds = [
        DDStatement('SYSTSPRT', FileDefinition('*', disposition='NEW')),
        DDStatement('SYSTSIN', FileDefinition(
            systsin_file,
            normal_disposition='SHR',
            status_group='OLD'
        )),
        DDStatement('SYSPRINT', FileDefinition('*', disposition='NEW')),
        DDStatement('SYSUDUMP', FileDefinition('*', disposition='NEW')),
        DDStatement('SYSIN', FileDefinition(
            sysin_file,
            normal_disposition='SHR',
            status_group='OLD'
        ))
    ]
    
    try:
        if verbose:
            print("Executing IKJEFT1B via mvscmdauth...")
        
        # Execute IKJEFT1B using mvscmdauth
        response = mvscmd.execute_authorized(
            pgm='IKJEFT1B',
            dds=dds,
            verbose=verbose
        )
        
        # Display output
        if response.stdout_response:
            print(response.stdout_response)
        
        if response.stderr_response:
            print(response.stderr_response, file=sys.stderr)
        
        if verbose:
            print(f"\nReturn code: {response.rc}")
        
        return response.rc
        
    except Exception as e:
        print(f"ERROR: Failed to execute IKJEFT1B: {e}", file=sys.stderr)
        return 16


def main():
    """Main entry point"""
    parser = argparse.ArgumentParser(
        description='Execute DB2 commands via IKJEFT1B',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Using regular files
  db2cmd --systsin systsin.txt --sysin sql.txt
  
  # Using named pipes
  mkfifo /tmp/systsin.pipe /tmp/sysin.pipe
  db2cmd --systsin /tmp/systsin.pipe --sysin /tmp/sysin.pipe
  
  # With verbose output
  db2cmd --systsin systsin.txt --sysin sql.txt --verbose
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
        '-v', '--verbose',
        action='store_true',
        help='Enable verbose output'
    )
    
    args = parser.parse_args()
    
    # Execute the DB2 command
    rc = execute_db2_command(args.systsin, args.sysin, args.verbose)
    
    return rc


if __name__ == '__main__':
    sys.exit(main())