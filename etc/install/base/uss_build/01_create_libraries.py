#!/usr/bin/env python3
"""
CBSA Library Creation Script
Creates only the necessary MVS datasets for VSAM files
Note: Source files, object files, and DBRMs remain in USS
"""

import sys
import os
from cbsa_utils import BuildConfig, MVSCommand, print_banner, print_step, check_prerequisites


def create_libraries(config: BuildConfig, verbose: bool = False) -> bool:
    """Create only required CBSA libraries (VSAM-related only)"""
    
    print_banner("CBSA Library Creation")
    
    print("Note: With USS-based build system, only VSAM-related datasets are needed.")
    print("Source files, object files, and DBRMs remain in USS file system.\n")
    
    # Only create libraries that are actually needed for VSAM files
    # All compilation artifacts (source, objects, DBRMs, load modules) stay in USS
    libraries = []
    
    # Check if we need any MVS datasets at all
    # For a pure USS build, we might not need any
    if not libraries:
        print("✓ No MVS datasets required for USS-based build")
        print("  All build artifacts will be in USS under build/ directory")
        return True
    
    success_count = 0
    fail_count = 0
    
    for i, lib in enumerate(libraries, 1):
        print_step(i, f"Creating {lib['desc']}")
        print(f"Dataset: {lib['name']}")
        
        if MVSCommand.allocate_pds(
            lib['name'],
            recfm=lib['recfm'],
            lrecl=lib['lrecl'],
            blksize=lib['blksize'],
            space=lib['space'],
            verbose=verbose
        ):
            print(f"✓ Successfully created {lib['name']}")
            success_count += 1
        else:
            print(f"✗ Failed to create {lib['name']}")
            fail_count += 1
    
    print(f"\n{'='*60}")
    print(f"Summary: {success_count} succeeded, {fail_count} failed")
    print(f"{'='*60}\n")
    
    return fail_count == 0


def setup_uss_directories(config: BuildConfig, verbose: bool = False) -> bool:
    """Create USS build directories"""
    
    print_banner("Setting Up USS Build Directories")
    
    # Create build directories in USS
    directories = [
        'build',
        'build/obj',
        'build/load',
        'build/dbrm',
        'build/dsect',
        'build/bind'
    ]
    
    success_count = 0
    fail_count = 0
    
    for i, directory in enumerate(directories, 1):
        print_step(i, f"Creating directory: {directory}")
        
        try:
            os.makedirs(directory, exist_ok=True)
            print(f"✓ Created {directory}")
            success_count += 1
        except Exception as e:
            print(f"✗ Failed to create {directory}: {e}")
            fail_count += 1
    
    print(f"\n{'='*60}")
    print(f"Summary: {success_count} directories created, {fail_count} failed")
    print(f"{'='*60}\n")
    
    return fail_count == 0


def main():
    """Main execution"""
    import argparse
    
    parser = argparse.ArgumentParser(description='Setup CBSA USS build environment')
    parser.add_argument('-c', '--config', default='build.conf', help='Configuration file')
    parser.add_argument('-v', '--verbose', action='store_true', help='Verbose output')
    
    args = parser.parse_args()
    
    # Check prerequisites
    if not check_prerequisites():
        return 1
    
    # Load configuration
    try:
        config = BuildConfig(args.config)
    except Exception as e:
        print(f"ERROR: Failed to load configuration: {e}")
        return 1
    
    # Create MVS libraries (if any are needed)
    if not create_libraries(config, args.verbose):
        print("ERROR: Library creation failed")
        return 1
    
    # Setup USS directories
    if not setup_uss_directories(config, args.verbose):
        print("ERROR: USS directory setup failed")
        return 1
    
    print("\n✓ USS build environment setup completed successfully!")
    print("\nNext steps:")
    print("  1. Run 'make setup-db2' to create DB2 artifacts")
    print("  2. Run 'make compile' to compile programs")
    print("  3. Run 'make bind' to bind to DB2")
    print("  4. Run 'make populate' to populate data")
    return 0


if __name__ == '__main__':
    sys.exit(main())

# Made with Bob
