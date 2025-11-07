#!/usr/bin/env python3
"""
CBSA Library Creation Script
Equivalent to CRELIBS.jcl - Creates all necessary datasets/libraries
"""

import sys
import os
from cbsa_utils import BuildConfig, MVSCommand, print_banner, print_step, check_prerequisites


def create_libraries(config: BuildConfig, verbose: bool = False) -> bool:
    """Create all required CBSA libraries"""
    
    print_banner("CBSA Library Creation")
    
    # Define all libraries to create
    libraries = [
        {
            'name': config.get('DB2_JCL_INSTALL'),
            'desc': 'DB2 JCL Installation Library',
            'recfm': 'FB',
            'lrecl': 80,
            'blksize': 27920,
            'space': 'CYL(5,2,20)'
        },
        {
            'name': config.get('BUILD_JCL'),
            'desc': 'Build JCL Library',
            'recfm': 'FB',
            'lrecl': 80,
            'blksize': 27920,
            'space': 'CYL(10,5,50)'
        },
        {
            'name': config.get('LOADLIB'),
            'desc': 'Load Module Library',
            'recfm': 'U',
            'lrecl': 0,
            'blksize': 32760,
            'space': 'CYL(50,10,100)'
        },
        {
            'name': config.get('DBRM'),
            'desc': 'DBRM Library',
            'recfm': 'FB',
            'lrecl': 80,
            'blksize': 27920,
            'space': 'CYL(10,5,50)'
        },
        {
            'name': config.get('LKED'),
            'desc': 'Link Edit Source Library',
            'recfm': 'FB',
            'lrecl': 80,
            'blksize': 27920,
            'space': 'CYL(5,2,20)'
        },
        {
            'name': config.get('BMS'),
            'desc': 'BMS Map Source Library',
            'recfm': 'FB',
            'lrecl': 80,
            'blksize': 27920,
            'space': 'CYL(5,2,20)'
        },
        {
            'name': config.get('ASM'),
            'desc': 'Assembler Source Library',
            'recfm': 'FB',
            'lrecl': 80,
            'blksize': 27920,
            'space': 'CYL(2,1,10)'
        },
        {
            'name': config.get('CBSAMOD'),
            'desc': 'COBOL Object Module Library',
            'recfm': 'FB',
            'lrecl': 80,
            'blksize': 27920,
            'space': 'CYL(20,10,50)'
        },
        {
            'name': config.get('COBOL'),
            'desc': 'COBOL Source Library',
            'recfm': 'FB',
            'lrecl': 80,
            'blksize': 27920,
            'space': 'CYL(10,5,50)'
        },
        {
            'name': config.get('DSECT'),
            'desc': 'Copybook/DSECT Library',
            'recfm': 'FB',
            'lrecl': 80,
            'blksize': 27920,
            'space': 'CYL(5,2,20)'
        }
    ]
    
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


def copy_source_files(config: BuildConfig, verbose: bool = False) -> bool:
    """Copy source files from USS to MVS datasets"""
    
    print_banner("Copying Source Files to Datasets")
    
    # Define source to target mappings
    mappings = [
        {
            'source_dir': 'src/base/cobol_src',
            'target_ds': config.get('COBOL'),
            'pattern': '*.cbl',
            'desc': 'COBOL source files'
        },
        {
            'source_dir': 'src/base/cobol_copy',
            'target_ds': config.get('DSECT'),
            'pattern': '*.cpy',
            'desc': 'COBOL copybooks'
        },
        {
            'source_dir': 'src/base/bms_src',
            'target_ds': config.get('BMS'),
            'pattern': '*.bms',
            'desc': 'BMS map source'
        },
        {
            'source_dir': 'etc/install/base/linkeditjcl',
            'target_ds': config.get('LKED'),
            'pattern': '*.lked',
            'desc': 'Link edit control cards'
        },
        {
            'source_dir': 'etc/install/base/buildjcl',
            'target_ds': config.get('BUILD_JCL'),
            'pattern': '*.jcl',
            'desc': 'Build JCL members'
        },
        {
            'source_dir': 'etc/install/base/db2jcl',
            'target_ds': config.get('DB2_JCL_INSTALL'),
            'pattern': '*.jcl',
            'desc': 'DB2 JCL members'
        }
    ]
    
    success_count = 0
    fail_count = 0
    
    for i, mapping in enumerate(mappings, 1):
        print_step(i, f"Copying {mapping['desc']}")
        print(f"From: {mapping['source_dir']}")
        print(f"To:   {mapping['target_ds']}")
        
        source_dir = mapping['source_dir']
        if not os.path.exists(source_dir):
            print(f"⚠ Source directory not found: {source_dir}")
            continue
        
        # Get list of files matching pattern
        import glob
        pattern = os.path.join(source_dir, mapping['pattern'])
        files = glob.glob(pattern)
        
        if not files:
            print(f"⚠ No files found matching pattern: {pattern}")
            continue
        
        print(f"Found {len(files)} files to copy")
        
        for file_path in files:
            # Extract member name (filename without extension)
            member = os.path.splitext(os.path.basename(file_path))[0].upper()
            
            if verbose:
                print(f"  Copying {os.path.basename(file_path)} -> {member}")
            
            if MVSCommand.copy_member(file_path, mapping['target_ds'], member, verbose):
                success_count += 1
            else:
                print(f"  ✗ Failed to copy {file_path}")
                fail_count += 1
        
        print(f"✓ Completed copying {mapping['desc']}")
    
    print(f"\n{'='*60}")
    print(f"Summary: {success_count} files copied, {fail_count} failed")
    print(f"{'='*60}\n")
    
    return fail_count == 0


def main():
    """Main execution"""
    import argparse
    
    parser = argparse.ArgumentParser(description='Create CBSA libraries and copy source files')
    parser.add_argument('-c', '--config', default='build.conf', help='Configuration file')
    parser.add_argument('-v', '--verbose', action='store_true', help='Verbose output')
    parser.add_argument('--skip-copy', action='store_true', help='Skip copying source files')
    parser.add_argument('--copy-only', action='store_true', help='Only copy files, skip library creation')
    
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
    
    # Create libraries
    if not args.copy_only:
        if not create_libraries(config, args.verbose):
            print("ERROR: Library creation failed")
            return 1
    
    # Copy source files
    if not args.skip_copy:
        if not copy_source_files(config, args.verbose):
            print("ERROR: Source file copy failed")
            return 1
    
    print("\n✓ Library creation and setup completed successfully!")
    return 0


if __name__ == '__main__':
    sys.exit(main())

# Made with Bob
