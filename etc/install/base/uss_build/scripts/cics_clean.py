#!/usr/bin/env python3
"""
CBSA CICS Cleanup Script
Handles deletion of CICS datasets for clean reinstallation
- Deletes CICS CSD (DFHCSD) dataset if it exists
- Ensures clean state for subsequent installations
Uses Z Open Automation Utilities (ZOAU) for z/OS operations
"""

import sys
import argparse
from pathlib import Path
from cbsa_utils import BuildConfig, print_banner, print_step

try:
    from zoautil_py import datasets
except ImportError:
    print("ERROR: zoautil_py module not found. Please ensure ZOAU is properly installed.")
    sys.exit(1)


def delete_csd_dataset(csd_dataset: str, verbose: bool = False) -> bool:
    """
    Delete CICS CSD dataset if it exists
    
    Args:
        csd_dataset: Name of the CSD dataset to delete
        verbose: Enable verbose output
    
    Returns:
        True if dataset was deleted or didn't exist, False on error
    """
    
    print_step(1, "Checking CSD Dataset")
    print(f"Dataset: {csd_dataset}")
    
    try:
        # Check if dataset exists
        if not datasets.exists(csd_dataset):
            print(f"✓ CSD dataset does not exist: {csd_dataset}")
            return True
        
        if verbose:
            print(f"Deleting CSD dataset: {csd_dataset}")
        
        # Delete the dataset
        datasets.delete(csd_dataset)
        
        print(f"✓ CSD dataset deleted: {csd_dataset}")
        
        if verbose:
            print(f"  Dataset will be re-allocated on next install")
            print(f"  INITIALIZE will be performed automatically")
        
        return True
        
    except Exception as e:
        print(f"✗ Failed to delete CSD dataset: {e}")
        if verbose:
            import traceback
            traceback.print_exc()
        return False


def main():
    """Main entry point for CICS cleanup"""
    
    parser = argparse.ArgumentParser(
        description='CBSA CICS Cleanup - Delete CICS CSD dataset',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  %(prog)s --config build.conf
  %(prog)s --config build.conf --verbose

This script deletes the CICS CSD dataset to ensure a clean reinstallation.
The dataset will be re-allocated and initialized on the next 'make install'.
        """
    )
    
    parser.add_argument(
        '-c', '--config',
        required=True,
        help='Path to build configuration file (build.conf)'
    )
    
    parser.add_argument(
        '-v', '--verbose',
        action='store_true',
        help='Enable verbose output'
    )
    
    args = parser.parse_args()
    
    # Validate config file exists
    if not Path(args.config).exists():
        print(f"ERROR: Configuration file not found: {args.config}")
        sys.exit(1)
    
    # Load configuration
    try:
        config = BuildConfig(args.config)
    except Exception as e:
        print(f"ERROR: Failed to load configuration: {e}")
        sys.exit(1)
    
    # Print banner
    print_banner("CBSA CICS Cleanup")
    
    if args.verbose:
        print(f"Configuration file: {args.config}")
        print(f"CSD Dataset: {config.get('CSD_DATASET')}")
        print()
    
    # Delete CSD dataset
    csd_dataset = config.get('CSD_DATASET')
    if not csd_dataset:
        print("ERROR: CSD_DATASET not defined in configuration file")
        sys.exit(1)
    
    success = delete_csd_dataset(csd_dataset, verbose=args.verbose)
    
    if success:
        print()
        print("=" * 70)
        print("CICS Cleanup Complete!")
        print("=" * 70)
        print()
        print("Next steps:")
        print("  Run 'make install' or 'make cics-create' to re-allocate and initialize CSD")
        print()
        sys.exit(0)
    else:
        print()
        print("=" * 70)
        print("CICS Cleanup Failed!")
        print("=" * 70)
        print()
        sys.exit(1)


if __name__ == '__main__':
    main()

# Made with Bob
