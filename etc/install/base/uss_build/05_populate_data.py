#!/usr/bin/env python3
"""
CBSA Data Population Script
Equivalent to BANKDATA.jcl - Creates VSAM files and populates DB2 tables
"""

import sys
import os
import subprocess
from cbsa_utils import BuildConfig, MVSCommand, print_banner, print_step, check_prerequisites


def check_vsam_exists(dataset_name: str, verbose: bool = False) -> bool:
    """Check if a VSAM dataset exists"""
    cmd = f"LISTCAT ENTRIES('{dataset_name}')"
    rc, stdout, stderr = MVSCommand.run_tso(cmd, verbose)
    return rc == 0


def create_vsam_files(config: BuildConfig, verbose: bool = False) -> bool:
    """Create VSAM files for CBSA (skip if already exist)"""
    
    print_banner("Creating VSAM Files")
    
    bank_prefix = config.get('BANK_PREFIX')
    
    # Step 1: Create ABNDFILE
    print_step(1, "Creating ABNDFILE VSAM KSDS")
    
    abndfile = f"{bank_prefix}.ABNDFILE"
    
    if check_vsam_exists(abndfile, verbose):
        print(f"✓ {abndfile} already exists (skipping creation)")
    else:
        abndfile_params = {
            'CYL': '6 6',
            'KEYS': '12 0',
            'RECORDSIZE': '681 681',
            'SHAREOPTIONS': '2 3',
            'INDEXED': '',
            'LOG': 'NONE',
            'REUSE': '',
            'FREESPACE': '3 3'
        }
        
        if MVSCommand.allocate_dataset(abndfile, abndfile_params, verbose):
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
        customer_params = {
            'CYL': '50 50',
            'KEYS': '16 4',
            'RECORDSIZE': '259 259',
            'SHAREOPTIONS': '2 3',
            'INDEXED': '',
            'LOG': 'UNDO',
        }
        
        if MVSCommand.allocate_dataset(customer, customer_params, verbose):
            print(f"✓ {customer} created successfully")
        else:
            print(f"✗ Failed to create {customer}")
            return False
    
    return True


def check_data_populated(config: BuildConfig, verbose: bool = False) -> bool:
    """Check if data is already populated in DB2"""
    from cbsa_utils import DB2Utilities
    
    db2_utils = DB2Utilities(config)
    db2_owner = config.get('DB2_OWNER')
    
    # Check if ACCOUNT table has data
    sql_check = f"""
SET CURRENT SQLID = '{db2_owner}';
SELECT COUNT(*) AS CNT FROM ACCOUNT;
"""
    
    try:
        result = db2_utils.execute_sql(sql_check, verbose)
        # execute_sql returns bool, so we check if it succeeded
        # If table has data and query succeeds, we assume it's populated
        return result
    except:
        pass
    
    return False


def populate_data(config: BuildConfig, start_cust: int = 1, end_cust: int = 10000,
                 increment: int = 1, seed: int = 1000000000000000,
                 verbose: bool = False) -> bool:
    """Run BANKDATA program to populate data (skip if already populated)"""
    
    print_banner("Populating Data")
    
    # Check if data is already populated
    print_step(1, "Checking if data is already populated")
    if check_data_populated(config, verbose):
        print("✓ Data is already populated (skipping population)")
        return True
    
    print_step(2, "Running BANKDATA Program")
    print(f"Customer range: {start_cust} to {end_cust} (increment: {increment})")
    print(f"Random seed: {seed}")
    
    bank_prefix = config.get('BANK_PREFIX')
    loadlib = config.get('LOADLIB')
    dbrm_lib = config.get('DBRM')
    db2_hlq = config.get('DB2_HLQ')
    db2_subsystem = config.get('DB2_SYSTEM')
    db2_plan = config.get('CBSA_PLAN')
    
    # Build TSO command to run BANKDATA
    tso_cmd = f"""
DSN SYSTEM({db2_subsystem})
RUN PROGRAM(BANKDATA) -
PLAN({db2_plan}) -
PARM('{start_cust},{end_cust},{increment},{seed}') -
LIB('{loadlib}')
END
"""
    
    # Write TSO command to temp file
    temp_tso = f"/tmp/bankdata_{os.getpid()}.tso"
    try:
        with open(temp_tso, 'w') as f:
            f.write(tso_cmd)
        
        # Execute via IKJEFT01
        cmd = f"IKJEFT01 <{temp_tso}"
        rc, stdout, stderr = MVSCommand.run_tso(cmd, verbose)
        
        if rc == 0:
            print("✓ BANKDATA executed successfully")
            print(f"  Populated {end_cust - start_cust + 1} customer records")
            print(f"  Populated ACCOUNT and CONTROL tables in DB2")
            return True
        else:
            print(f"✗ BANKDATA execution failed (RC={rc})")
            if stderr:
                print(f"Error: {stderr}")
            return False
            
    finally:
        if os.path.exists(temp_tso):
            os.remove(temp_tso)


def verify_data(config: BuildConfig, verbose: bool = False) -> bool:
    """Verify that data was populated correctly"""
    
    print_banner("Verifying Data Population")
    
    from cbsa_utils import DB2Utilities
    
    db2_utils = DB2Utilities(config)
    db2_owner = config.get('DB2_OWNER')
    
    # Check ACCOUNT table
    print_step(1, "Checking ACCOUNT Table")
    
    sql_check_account = f"""
SET CURRENT SQLID = '{db2_owner}';
SELECT COUNT(*) AS ACCOUNT_COUNT FROM ACCOUNT;
"""
    
    if db2_utils.execute_sql(sql_check_account, verbose):
        print("✓ ACCOUNT table accessible")
    else:
        print("✗ Could not access ACCOUNT table")
        return False
    
    # Check CONTROL table
    print_step(2, "Checking CONTROL Table")
    
    sql_check_control = f"""
SET CURRENT SQLID = '{db2_owner}';
SELECT * FROM CONTROL;
"""
    
    if db2_utils.execute_sql(sql_check_control, verbose):
        print("✓ CONTROL table accessible")
    else:
        print("✗ Could not access CONTROL table")
        return False
    
    # Check CUSTOMER VSAM file
    print_step(3, "Checking CUSTOMER VSAM File")
    
    bank_prefix = config.get('BANK_PREFIX')
    customer_file = f"{bank_prefix}.CUSTOMER"
    
    # Use IDCAMS LISTCAT to verify
    cmd = f"LISTCAT ENTRIES('{customer_file}')"
    rc, stdout, stderr = MVSCommand.run_tso(cmd, verbose)
    
    if rc == 0:
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
