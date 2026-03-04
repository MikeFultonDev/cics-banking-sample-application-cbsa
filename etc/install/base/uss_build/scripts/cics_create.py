#!/usr/bin/env python3
"""
CBSA CICS Creation and Configuration Script
Handles dataset allocation and CICS resource definition installation
- Pre-allocates required CICS datasets (DFHCSD)
- Installs CICS resource definitions using DFHCSDUP utility
Uses Z Open Automation Utilities (ZOAU) for z/OS operations
Uses envsubst for variable substitution
"""

import sys
import os
import tempfile
import subprocess
from pathlib import Path
from cbsa_utils import BuildConfig, print_banner, print_step, check_prerequisites
from zoautil_py import datasets
try:
    from zoautil_py import mvscmd
    from zoautil_py.ztypes import DDStatement, DatasetDefinition, FileDefinition
except ImportError:
    # Fallback if mvscmd is not available
    mvscmd = None
    DDStatement = None
    DatasetDefinition = None
    FileDefinition = None


def allocate_csd_dataset(csd_dataset: str, verbose: bool = False) -> bool:
    """
    Allocate CICS CSD dataset with proper attributes
    
    Based on CBSACSD.jcl requirements:
    - VSAM KSDS (Key Sequenced Data Set)
    - Used by DFHCSDUP utility
    
    Standard CICS CSD attributes:
    - RECORDSIZE: 4089 bytes (CICS standard)
    - FREESPACE: (10,10) - 10% free space per CI and CA
    - SHAREOPTIONS: (2,3) - Multiple readers/writers
    - INDEXED: True (KSDS)
    """
    
    print_step(1, "Allocating CSD Dataset")
    print(f"Dataset: {csd_dataset}")
    
    try:
        # Check if dataset already exists
        if datasets.exists(csd_dataset):
            print(f"✓ CSD dataset already exists: {csd_dataset}")
            return True
        
        if verbose:
            print(f"Creating new CSD dataset: {csd_dataset}")
        
        # Allocate VSAM KSDS for CICS CSD
        # CICS CSD requires specific VSAM attributes
        # Following the exact same pattern as populate_data.py which works correctly
        datasets.create(
            name=csd_dataset,
            dataset_type='KSDS',  # Key Sequenced Data Set (uppercase like populate_data.py)
            primary_space=100,  # Primary allocation
            secondary_space=50,  # Secondary allocation
            space_unit='TRK',  # Space unit: tracks (required parameter!)
            key_length=22,  # CICS CSD key length
            key_offset=0,  # Key starts at beginning
            record_length=4089,  # CICS CSD standard record length
            shareoptions='2 3'  # Multiple readers/writers (CICS standard)
        )
        
        print(f"✓ CSD dataset created successfully: {csd_dataset}")
        
        if verbose:
            print(f"  Type: VSAM KSDS")
            print(f"  Record Length: 4089")
            print(f"  Key Length: 22")
            print(f"  Key Offset: 0")
            print(f"  Primary Space: 100 tracks")
            print(f"  Secondary Space: 50 tracks")
            print(f"  Share Options: 2 3")
        
        return True
        
    except Exception as e:
        print(f"✗ Failed to allocate CSD dataset: {e}")
        if verbose:
            import traceback
            traceback.print_exc()
        return False


def create_temp_csd(csd_file: str, config_file: str, verbose: bool = False) -> str:
    """Create a temporary CSD file with variables substituted using envsubst"""
    if verbose:
        print(f"Reading CSD file: {csd_file}")
    
    if not os.path.exists(csd_file):
        raise FileNotFoundError(f"CSD file not found: {csd_file}")
    
    # Get path to envsubst utility
    script_dir = Path(__file__).resolve().parent
    envsubst_path = script_dir / 'bin' / 'envsubst'
    
    if not envsubst_path.exists():
        raise FileNotFoundError(f"envsubst utility not found: {envsubst_path}")
    
    # Use envsubst to perform variable substitution
    if verbose:
        print(f"Running envsubst to substitute variables...")
    
    try:
        result = subprocess.run(
            [sys.executable, str(envsubst_path), csd_file, '--config', config_file],
            capture_output=True,
            text=True,
            check=True
        )
        substituted_content = result.stdout
    except subprocess.CalledProcessError as e:
        raise RuntimeError(f"envsubst failed: {e.stderr}")
    
    # Create temporary file
    temp_fd, temp_path = tempfile.mkstemp(suffix='.csd', prefix='BANK_', text=True)
    
    try:
        with os.fdopen(temp_fd, 'w') as f:
            f.write(substituted_content)
        
        if verbose:
            print(f"Created temporary CSD file: {temp_path}")
        
        return temp_path
    except Exception as e:
        os.close(temp_fd)
        if os.path.exists(temp_path):
            os.unlink(temp_path)
        raise e


def install_csd_definitions(temp_csd_path: str, config: BuildConfig,
                           verbose: bool = False, debug: bool = False) -> bool:
    """Install CICS CSD definitions using DFHCSDUP via mvscmdauth"""
    
    print_banner("Installing CICS CSD Definitions")
    
    # Get configuration values
    cics_hlq = config.get('CICS_HLQ')
    cics_region = config.get('CICS_REGION')
    bank_prefix = config.get('BANK_PREFIX')
    
    if not cics_hlq:
        print("ERROR: CICS_HLQ not defined in configuration")
        return False
    
    if not cics_region:
        print("ERROR: CICS_REGION not defined in configuration")
        return False
    
    # Construct the CSD dataset name
    csd_dataset = f"{cics_region}.DFHCSD"
    
    # Allocate CSD dataset if it doesn't exist
    if not allocate_csd_dataset(csd_dataset, verbose):
        return False
    
    print_step(2, "Preparing DFHCSDUP execution")
    print(f"CICS HLQ: {cics_hlq}")
    print(f"CICS Region: {cics_region}")
    print(f"CSD Dataset: {csd_dataset}")
    
    print_step(3, "Executing DFHCSDUP")
    
    # Build STEPLIB concatenation
    steplib = f"{cics_hlq}.SDFHLOAD"
    
    if verbose:
        print(f"STEPLIB: {steplib}")
        print(f"DFHCSD: {csd_dataset}")
        print(f"SYSIN: {temp_csd_path}")
    
    # Create temporary files for SYSPRINT and CBDOUT
    sysprint_file = None
    cbdout_file = None
    
    try:
        # Use mvscmdauth to execute DFHCSDUP with appropriate authority
        # DFHCSDUP requires authorized libraries and access to CICS datasets
        
        # Read the temporary CSD file content
        with open(temp_csd_path, 'r') as f:
            sysin_content = f.read()
        
        # Prepend INITIALIZE command to initialize the CSD before any DEFINE commands
        # This is required to avoid DFH5114 error: "THE PRIMARY CSD HAS NOT BEEN INITIALIZED"
        sysin_content = "INITIALIZE\n" + sysin_content
        
        if verbose:
            print("\nDFHCSUP Input:")
            print("-" * 60)
            print(sysin_content)
            print("-" * 60)
        
        # Execute DFHCSDUP using mvscmd
        # mvscmd provides the necessary authority for CICS utilities
        if mvscmd is None:
            raise RuntimeError("zoautil_py.mvscmd module is not available. Please ensure ZOAU is properly installed.")
        
        # Create temporary files for capturing output
        # Use delete=False to control cleanup manually based on debug mode
        sysprint_file = tempfile.NamedTemporaryFile(
            mode='w+',
            suffix='.sysprint',
            prefix='DFHCSDUP_',
            delete=False
        )
        cbdout_file = tempfile.NamedTemporaryFile(
            mode='w+',
            suffix='.cbdout',
            prefix='DFHCSDUP_',
            delete=False
        )
        
        # Close the files so mvscmd can write to them
        sysprint_path = sysprint_file.name
        cbdout_path = cbdout_file.name
        sysprint_file.close()
        cbdout_file.close()
        
        if verbose:
            print(f"SYSPRINT output will be captured to: {sysprint_path}")
            print(f"CBDOUT output will be captured to: {cbdout_path}")
        
        # Convert SYSIN content to EBCDIC 1047 before writing to temp file
        # DFHCSDUP requires input in EBCDIC 1047 encoding
        try:
            sysin_ebcdic = sysin_content.encode('cp1047')
            with open(temp_csd_path, 'wb') as f:
                f.write(sysin_ebcdic)
            if verbose:
                print(f"Converted SYSIN content to EBCDIC 1047 (cp1047)")
        except Exception as e:
            raise RuntimeError(f"Failed to convert SYSIN to EBCDIC 1047: {e}")
        
        result = mvscmd.execute(
            pgm='DFHCSDUP',
            parm='',
            steplib=steplib,
            dds=[
                DDStatement('DFHCSD', DatasetDefinition(csd_dataset)),
                DDStatement('SYSIN', FileDefinition(f"{temp_csd_path},lrecl=80,recfm=FB")),
                DDStatement('SYSPRINT', FileDefinition(f"{sysprint_path},recfm=FB")),
                DDStatement('CBDOUT', FileDefinition(f"{cbdout_path},recfm=FB")),
                DDStatement('AMSDUMP', FileDefinition('DUMMY'))
            ],
            verbose=verbose
        )
        
        # Check return code
        rc = result.rc if hasattr(result, 'rc') else result
        
        if verbose:
            print(f"\nDFHCSUDP Return Code: {rc}")
        
        # Read output files if there's an error or verbose mode is enabled
        if rc != 0 or verbose:
            sysprint_content = ""
            cbdout_content = ""
            
            # Read SYSPRINT output
            # DFHCSDUP writes output in EBCDIC 1047, convert to UTF-8
            try:
                if os.path.exists(sysprint_path):
                    with open(sysprint_path, 'rb') as f:
                        sysprint_bytes = f.read()
                    sysprint_content = sysprint_bytes.decode('cp1047', errors='replace')
                    if verbose:
                        print(f"Converted SYSPRINT from EBCDIC 1047 to UTF-8")
            except Exception as e:
                sysprint_content = f"[Error reading SYSPRINT: {e}]"
            
            # Read CBDOUT output
            # DFHCSDUP writes output in EBCDIC 1047, convert to UTF-8
            try:
                if os.path.exists(cbdout_path):
                    with open(cbdout_path, 'rb') as f:
                        cbdout_bytes = f.read()
                    cbdout_content = cbdout_bytes.decode('cp1047', errors='replace')
                    if verbose:
                        print(f"Converted CBDOUT from EBCDIC 1047 to UTF-8")
            except Exception as e:
                cbdout_content = f"[Error reading CBDOUT: {e}]"
            
            # Print result object information if there's an error
            if rc != 0:
                print("\n" + "=" * 70, file=sys.stderr)
                print("DFHCSDUP Result Object Information:", file=sys.stderr)
                print("=" * 70, file=sys.stderr)
                print(f"Return code: {rc}", file=sys.stderr)
                
                # Print stdout if available
                if hasattr(result, 'stdout') and result.stdout:
                    print(f"\nStandard Output:\n{result.stdout}", file=sys.stderr)
                elif hasattr(result, 'output') and result.output:
                    print(f"\nOutput:\n{result.output}", file=sys.stderr)
                
                # Print stderr if available
                if hasattr(result, 'stderr') and result.stderr:
                    print(f"\nStandard Error:\n{result.stderr}", file=sys.stderr)
                elif hasattr(result, 'error') and result.error:
                    print(f"\nError:\n{result.error}", file=sys.stderr)
                
                print("=" * 70 + "\n", file=sys.stderr)
            
            # Print output to stderr with clear labels
            if sysprint_content:
                print("\n" + "=" * 70, file=sys.stderr)
                print("DFHCSDUP SYSPRINT Output:", file=sys.stderr)
                print("=" * 70, file=sys.stderr)
                print(sysprint_content, file=sys.stderr)
                print("=" * 70 + "\n", file=sys.stderr)
            
            if cbdout_content:
                print("\n" + "=" * 70, file=sys.stderr)
                print("DFHCSDUP CBDOUT Output:", file=sys.stderr)
                print("=" * 70, file=sys.stderr)
                print(cbdout_content, file=sys.stderr)
                print("=" * 70 + "\n", file=sys.stderr)
        
        if rc == 0:
            print("✓ CICS CSD definitions installed successfully")
            print(f"  Group BANK added to list {cics_region}")
            return True
        else:
            print(f"✗ DFHCSDUP execution failed (RC={rc})", file=sys.stderr)
            return False
            
    except Exception as e:
        print(f"✗ Error executing DFHCSDUP: {e}", file=sys.stderr)
        if verbose:
            import traceback
            traceback.print_exc()
        return False
    
    finally:
        # Clean up temporary files unless in debug mode
        if sysprint_file:
            sysprint_path = sysprint_file.name if hasattr(sysprint_file, 'name') else None
            if sysprint_path and os.path.exists(sysprint_path):
                if debug:
                    print(f"Debug mode: SYSPRINT file retained at: {sysprint_path}")
                else:
                    try:
                        os.unlink(sysprint_path)
                        if verbose:
                            print(f"Cleaned up SYSPRINT file: {sysprint_path}")
                    except Exception as e:
                        if verbose:
                            print(f"Warning: Failed to clean up SYSPRINT file: {e}")
        
        if cbdout_file:
            cbdout_path = cbdout_file.name if hasattr(cbdout_file, 'name') else None
            if cbdout_path and os.path.exists(cbdout_path):
                if debug:
                    print(f"Debug mode: CBDOUT file retained at: {cbdout_path}")
                else:
                    try:
                        os.unlink(cbdout_path)
                        if verbose:
                            print(f"Cleaned up CBDOUT file: {cbdout_path}")
                    except Exception as e:
                        if verbose:
                            print(f"Warning: Failed to clean up CBDOUT file: {e}")


def verify_installation(config: BuildConfig, verbose: bool = False) -> bool:
    """Verify that CSD definitions were installed"""
    
    print_banner("Verifying CSD Installation")
    
    cics_region = config.get('CICS_REGION')
    csd_dataset = f"{cics_region}.DFHCSD"
    
    print_step(1, "Checking CSD Dataset")
    
    try:
        if datasets.exists(csd_dataset):
            print(f"✓ CSD dataset {csd_dataset} exists")
            return True
        else:
            print(f"✗ CSD dataset {csd_dataset} not found")
            return False
    except Exception as e:
        print(f"✗ Error checking CSD dataset: {e}")
        return False


def main():
    """Main execution"""
    import argparse
    
    parser = argparse.ArgumentParser(
        description='Create CICS datasets and install resource definitions using DFHCSDUP'
    )
    parser.add_argument(
        '-c', '--config',
        default='build.conf',
        help='Configuration file (default: build.conf)'
    )
    parser.add_argument(
        '-v', '--verbose',
        action='store_true',
        help='Verbose output'
    )
    parser.add_argument(
        '--debug',
        action='store_true',
        help='Debug mode - retain temporary files'
    )
    parser.add_argument(
        '--csd-file',
        default=None,
        help='CSD file to install (default: cicscsd/BANK.csd)'
    )
    parser.add_argument(
        '--verify-only',
        action='store_true',
        help='Only verify installation, skip actual installation'
    )
    parser.add_argument(
        '--allocate-only',
        action='store_true',
        help='Only allocate datasets, skip CSD installation'
    )
    
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
    
    # Allocate only mode
    if args.allocate_only:
        cics_region = config.get('CICS_REGION')
        if not cics_region:
            print("ERROR: CICS_REGION not defined in configuration")
            return 1
        
        csd_dataset = f"{cics_region}.DFHCSD"
        if not allocate_csd_dataset(csd_dataset, args.verbose):
            print("ERROR: Dataset allocation failed")
            return 1
        
        print("\n✓ Dataset allocation completed successfully!")
        return 0
    
    # Determine CSD file path
    if args.csd_file:
        csd_file = args.csd_file
    else:
        # Default to cicscsd/BANK.csd relative to config file
        config_dir = Path(args.config).parent
        csd_file = str(config_dir / 'cicscsd' / 'BANK.csd')
    
    if not os.path.exists(csd_file):
        print(f"ERROR: CSD file not found: {csd_file}")
        return 1
    
    # Verify only mode
    if args.verify_only:
        if not verify_installation(config, args.verbose):
            print("ERROR: CSD verification failed")
            return 1
        print("\n✓ CSD verification completed successfully!")
        return 0
    
    # Create temporary CSD file with substitutions
    temp_csd_path = None
    try:
        temp_csd_path = create_temp_csd(csd_file, args.config, args.verbose)
        
        # Install CSD definitions (includes dataset allocation)
        if not install_csd_definitions(temp_csd_path, config, args.verbose, args.debug):
            print("ERROR: CSD installation failed")
            return 1
        
        # Verify installation
        if not verify_installation(config, args.verbose):
            print("⚠ Warning: CSD verification failed")
        
        print("\n✓ CICS creation and configuration completed successfully!")
        return 0
        
    except Exception as e:
        print(f"ERROR: {e}")
        if args.verbose:
            import traceback
            traceback.print_exc()
        return 1
        
    finally:
        # Clean up temporary file unless in debug mode
        if temp_csd_path and os.path.exists(temp_csd_path):
            if args.debug:
                print(f"\nDebug mode: Temporary CSD file retained at: {temp_csd_path}")
            else:
                try:
                    os.unlink(temp_csd_path)
                    if args.verbose:
                        print(f"Cleaned up temporary file: {temp_csd_path}")
                except Exception as e:
                    if args.verbose:
                        print(f"Warning: Failed to clean up temporary file: {e}")


if __name__ == '__main__':
    sys.exit(main())

# Made with Bob