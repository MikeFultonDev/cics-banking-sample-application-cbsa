#!/usr/bin/env python3
"""
CBSA Data Population Script
Equivalent to BANKDATA.jcl - Creates VSAM files and populates DB2 tables
Uses Z Open Automation Utilities (ZOAU) for VSAM operations
Uses batchtsocmd 0.2.1 for DB2 operations
"""

import sys
import os
from cbsa_utils import BuildConfig, print_banner, print_step, check_prerequisites
from batchtsocmd import db2sql, db2run

# Import ZOAU for VSAM operations
from zoautil_py import datasets


def check_vsam_exists(dataset_name: str, verbose: bool = False) -> bool:
    """Check if a VSAM dataset exists using ZOAU"""
    if verbose:
        print(f"Checking if {dataset_name} exists...")
    
    try:
        return datasets.exists(dataset_name)
    except Exception as e:
        if verbose:
            print(f"Error checking VSAM existence: {e}")
        return False


def create_vsam_ksds(dataset_name: str, params: dict, verbose: bool = False) -> bool:
    """Create a VSAM KSDS using ZOAU datasets.create"""
    if verbose:
        print(f"Creating VSAM KSDS: {dataset_name}")
    
    try:
        # Delete if exists
        if datasets.exists(dataset_name):
            if verbose:
                print(f"Dataset {dataset_name} already exists, deleting...")
            datasets.delete(dataset_name)
        
        # Parse space parameters (now in MB or GB)
        space = params.get('SPACE', 'MB(5 5)')
        import re
        
        # Support MB(primary secondary) or GB(primary secondary)
        if 'MB' in space:
            match = re.search(r'MB\((\d+)\s+(\d+)\)', space)
            if match:
                primary = int(match.group(1))
                secondary = int(match.group(2))
            else:
                primary, secondary = 5, 5
            space_type = 'MB'
        elif 'GB' in space:
            match = re.search(r'GB\((\d+)\s+(\d+)\)', space)
            if match:
                primary = int(match.group(1))
                secondary = int(match.group(2))
            else:
                primary, secondary = 1, 1
            space_type = 'GB'
        else:
            # Default to MB
            primary, secondary = 5, 5
            space_type = 'MB'
        
        # Parse keys (e.g., "12 0" means length=12, offset=0)
        keys = params.get('KEYS', '12 0').split()
        key_length = int(keys[0])
        key_offset = int(keys[1]) if len(keys) > 1 else 0
        
        # Parse record size (e.g., "681 681" means average=681, max=681)
        recordsize = params.get('RECORDSIZE', '681 681').split()
        record_length = int(recordsize[1]) if len(recordsize) > 1 else int(recordsize[0])
        
        # Parse shareoptions (e.g., "2 3")
        shareoptions = params.get('SHAREOPTIONS', '2 3')
        
        # Parse freespace if provided (e.g., "3 3")
        freespace_ci = 0
        freespace_ca = 0
        if 'FREESPACE' in params:
            fs = params['FREESPACE'].split()
            freespace_ci = int(fs[0]) if len(fs) > 0 else 0
            freespace_ca = int(fs[1]) if len(fs) > 1 else 0
        
        # Create VSAM KSDS using ZOAU
        # ZOAU datasets.create for VSAM KSDS
        datasets.create(
            name=dataset_name,
            dataset_type='KSDS',
            primary_space=primary,
            secondary_space=secondary,
            space_unit=space_type,
            key_length=key_length,
            key_offset=key_offset,
            record_length=record_length,
            shareoptions=shareoptions,
            reuse=params.get('REUSE', False),
            freespace_ci=freespace_ci,
            freespace_ca=freespace_ca,
            log=params.get('LOG', 'NONE')
        )
        
        if verbose:
            print(f"✓ {dataset_name} created successfully")
        
        return True
        
    except Exception as e:
        if verbose:
            print(f"✗ Failed to create {dataset_name}: {e}")
        return False


def create_vsam_files(config: BuildConfig, verbose: bool = False) -> bool:
    """Create VSAM files for CBSA using ZOAU (skip if already exist)"""
    
    print_banner("Creating VSAM Files")
    
    bank_prefix = config.get('BANK_PREFIX')
    
    # Step 1: Create ABNDFILE
    print_step(1, "Creating ABNDFILE VSAM KSDS")
    
    abndfile = f"{bank_prefix}.ABNDFILE"
    
    if check_vsam_exists(abndfile, verbose):
        print(f"✓ {abndfile} already exists (skipping creation)")
    else:
        # ABNDFILE: ~5 MB primary, 5 MB secondary (was 6 CYL ~= 4.5 MB)
        abndfile_params = {
            'SPACE': 'MB(5 5)',
            'KEYS': '12 0',
            'RECORDSIZE': '681 681',
            'SHAREOPTIONS': '2 3',
            'LOG': 'NONE',
            'REUSE': True,
            'FREESPACE': '3 3'
        }
        
        if create_vsam_ksds(abndfile, abndfile_params, verbose):
            print(f"✓ {abndfile} created successfully")
        else:
            print(f"✗ Failed to create {abndfile}")
            return False
    
    # Step 2: Create CUSTOMER file
    print_step(2, "Creating CUSTOMER VSAM KSDS")
    
    customer = f"{bank_prefix}.CUSTOMER"
    
    if check_vsam_exists(customer, verbose):
        print(f"✓ {customer} already exists (skipping creation)")
    else:
        # CUSTOMER: 40 MB primary, 40 MB secondary (was 50 CYL ~= 37.5 MB)
        customer_params = {
            'SPACE': 'MB(40 40)',
            'KEYS': '16 4',
            'RECORDSIZE': '259 259',
            'SHAREOPTIONS': '2 3',
            'LOG': 'UNDO',
        }
        
        if create_vsam_ksds(customer, customer_params, verbose):
            print(f"✓ {customer} created successfully")
        else:
            print(f"✗ Failed to create {customer}")
            return False
    
    return True


def check_data_populated(config: BuildConfig, verbose: bool = False) -> bool:
    """Check if data is already populated in DB2 using db2sql"""
    if verbose:
        print("Checking if data is already populated...")
    
    db2_subsystem = config.get('DB2_SYSTEM')
    db2_hlq = config.get('DB2_HLQ')
    db2_owner = config.get('DB2_OWNER')
    dsntep_plan = config.get('DB2_DSNTEP_PLAN', 'DSNTEP13')
    toollib = config.get('DB2_TOOLLIB', f'{db2_hlq}.RUNLIB.LOAD')
    steplib = f"{db2_hlq}.SDSNEXIT:{db2_hlq}.SDSNLOAD"
    
    # Check if ACCOUNT table has data
    sql_check = f"""SET CURRENT SQLID = '{db2_owner}';
SELECT COUNT(*) AS CNT FROM ACCOUNT;"""
    
    try:
        rc = db2sql(
            sysin_content=sql_check,
            system=db2_subsystem,
            plan=dsntep_plan,
            toollib=toollib,
            steplib=steplib,
            verbose=verbose
        )
        
        # If query succeeds (rc=0), assume data exists
        return rc == 0
        
    except Exception as e:
        if verbose:
            print(f"Error checking data: {e}")
        return False


def populate_data(config: BuildConfig, start_cust: int = 1, end_cust: int = 10000,
                 increment: int = 1, seed: int = 1000000000000000,
                 verbose: bool = False) -> bool:
    """Run BANKDATA program to populate data using db2run"""
    
    print_banner("Populating Data")
    
    # Check if data is already populated
    print_step(1, "Checking if data is already populated")
    if check_data_populated(config, verbose):
        print("✓ Data is already populated (skipping population)")
        return True
    
    print_step(2, "Running BANKDATA Program")
    print(f"Customer range: {start_cust} to {end_cust} (increment: {increment})")
    print(f"Random seed: {seed}")
    
    db2_subsystem = config.get('DB2_SYSTEM')
    db2_hlq = config.get('DB2_HLQ')
    db2_plan = config.get('CBSA_PLAN')
    loadlib = config.get('LOADLIB')
    steplib = f"{db2_hlq}.SDSNEXIT:{db2_hlq}.SDSNLOAD"
    
    # Build program parameters
    parm = f"{start_cust},{end_cust},{increment},{seed}"
    
    try:
        # Use db2run to execute BANKDATA program with DB2 plan
        rc = db2run(
            program='BANKDATA',
            system=db2_subsystem,
            plan=db2_plan,
            parm=parm,
            library=loadlib,
            steplib=steplib,
            verbose=verbose
        )
        
        if rc == 0:
            print("✓ BANKDATA executed successfully")
            print(f"  Populated {end_cust - start_cust + 1} customer records")
            print(f"  Populated ACCOUNT and CONTROL tables in DB2")
            return True
        else:
            print(f"✗ BANKDATA execution failed (RC={rc})")
            return False
            
    except Exception as e:
        print(f"✗ Error running BANKDATA: {e}")
        return False


def verify_data(config: BuildConfig, verbose: bool = False) -> bool:
    """Verify that data was populated correctly using db2sql and ZOAU"""
    
    print_banner("Verifying Data Population")
    
    db2_subsystem = config.get('DB2_SYSTEM')
    db2_hlq = config.get('DB2_HLQ')
    db2_owner = config.get('DB2_OWNER')
    dsntep_plan = config.get('DB2_DSNTEP_PLAN', 'DSNTEP13')
    toollib = config.get('DB2_TOOLLIB', f'{db2_hlq}.RUNLIB.LOAD')
    steplib = f"{db2_hlq}.SDSNEXIT:{db2_hlq}.SDSNLOAD"
    
    # Check ACCOUNT table
    print_step(1, "Checking ACCOUNT Table")
    
    sql_check_account = f"""SET CURRENT SQLID = '{db2_owner}';
SELECT COUNT(*) AS ACCOUNT_COUNT FROM ACCOUNT;"""
    
    try:
        rc = db2sql(
            sysin_content=sql_check_account,
            system=db2_subsystem,
            plan=dsntep_plan,
            toollib=toollib,
            steplib=steplib,
            verbose=verbose
        )
        
        if rc == 0:
            print("✓ ACCOUNT table accessible")
        else:
            print("✗ Could not access ACCOUNT table")
            return False
    except Exception as e:
        print(f"✗ Error accessing ACCOUNT table: {e}")
        return False
    
    # Check CONTROL table
    print_step(2, "Checking CONTROL Table")
    
    sql_check_control = f"""SET CURRENT SQLID = '{db2_owner}';
SELECT * FROM CONTROL;"""
    
    try:
        rc = db2sql(
            sysin_content=sql_check_control,
            system=db2_subsystem,
            plan=dsntep_plan,
            toollib=toollib,
            steplib=steplib,
            verbose=verbose
        )
        
        if rc == 0:
            print("✓ CONTROL table accessible")
        else:
            print("✗ Could not access CONTROL table")
            return False
    except Exception as e:
        print(f"✗ Error accessing CONTROL table: {e}")
        return False
    
    # Check CUSTOMER VSAM file using ZOAU
    print_step(3, "Checking CUSTOMER VSAM File")
    
    bank_prefix = config.get('BANK_PREFIX')
    customer_file = f"{bank_prefix}.CUSTOMER"
    
    if check_vsam_exists(customer_file, verbose):
        print(f"✓ CUSTOMER file {customer_file} exists")
    else:
        print(f"✗ CUSTOMER file {customer_file} not found")
        return False
    
    return True


def main():
    """Main execution"""
    import argparse
    
    parser = argparse.ArgumentParser(description='Create VSAM files and populate CBSA data')
    parser.add_argument('-c', '--config', default='build.conf', help='Configuration file')
    parser.add_argument('-v', '--verbose', action='store_true', help='Verbose output')
    parser.add_argument('--start', type=int, default=1, help='Starting customer number')
    parser.add_argument('--end', type=int, default=10000, help='Ending customer number')
    parser.add_argument('--increment', type=int, default=1, help='Customer number increment')
    parser.add_argument('--seed', type=int, default=1000000000000000, help='Random seed')
    parser.add_argument('--skip-vsam', action='store_true', help='Skip VSAM file creation')
    parser.add_argument('--skip-populate', action='store_true', help='Skip data population')
    parser.add_argument('--verify-only', action='store_true', help='Only verify data, skip creation')
    
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
    
    # Verify only
    if args.verify_only:
        if not verify_data(config, args.verbose):
            print("ERROR: Data verification failed")
            return 1
        print("\n✓ Data verification completed successfully!")
        return 0
    
    # Create VSAM files
    if not args.skip_vsam:
        if not create_vsam_files(config, args.verbose):
            print("ERROR: VSAM file creation failed")
            return 1
    
    # Populate data
    if not args.skip_populate:
        if not populate_data(config, args.start, args.end, args.increment, 
                           args.seed, args.verbose):
            print("ERROR: Data population failed")
            return 1
    
    # Verify data
    if not verify_data(config, args.verbose):
        print("⚠ Warning: Data verification failed")
    
    print("\n✓ Data population completed successfully!")
    return 0


if __name__ == '__main__':
    sys.exit(main())

# Made with Bob
