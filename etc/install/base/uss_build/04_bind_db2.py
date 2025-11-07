#!/usr/bin/env python3
"""
CBSA DB2 Bind Script
Equivalent to DB2BIND.jcl - Binds COBOL programs to DB2
"""

import sys
import os
from cbsa_utils import BuildConfig, DB2Utilities, print_banner, print_step, check_prerequisites


def bind_db2_plan(config: BuildConfig, verbose: bool = False) -> bool:
    """Bind DB2 plan and packages"""
    
    print_banner("DB2 Plan and Package Binding")
    
    db2_utils = DB2Utilities(config)
    
    dbrm_lib = config.get('DBRM')
    db2_plan = config.get('DB2_PLAN')
    db2_package = config.get('DB2_PACKAGE')
    db2_owner = config.get('DB2_OWNER')
    
    # Step 1: Bind packages
    print_step(1, "Binding DB2 Packages")
    
    # List of programs that need DB2 binding
    db2_programs = [
        'ABNDPROC',
        'BANKDATA',
        'CREACC',
        'CRECUST',
        'DBCRFUN',
        'DELACC',
        'DELCUS',
        'INQACC',
        'INQACCCU',
        'INQCUST',
        'UPDACC',
        'UPDCUST',
        'XFRFUN'
    ]
    
    success_count = 0
    fail_count = 0
    
    for program in db2_programs:
        if verbose:
            print(f"  Binding package for {program}...")
        
        sql_bind_package = f"""
BIND PACKAGE({db2_package}.{program})
     MEMBER({program})
     LIBRARY('{dbrm_lib}')
     OWNER({db2_owner})
     QUALIFIER({db2_owner})
     ACTION(REPLACE)
     ISOLATION(CS)
     RELEASE(COMMIT)
     VALIDATE(BIND)
     CURRENTDATA(NO)
     DYNAMICRULES(BIND)
     DEGREE(1)
     EXPLAIN(NO);
"""
        
        if db2_utils.execute_sql(sql_bind_package, verbose):
            if verbose:
                print(f"  ✓ Package {program} bound successfully")
            success_count += 1
        else:
            print(f"  ✗ Failed to bind package {program}")
            fail_count += 1
    
    print(f"\nPackage binding: {success_count} succeeded, {fail_count} failed")
    
    if fail_count > 0:
        return False
    
    # Step 2: Bind plan
    print_step(2, "Binding DB2 Plan")
    
    # Build package list
    package_list = ','.join([f'{db2_package}.{prog}' for prog in db2_programs])
    
    sql_bind_plan = f"""
BIND PLAN({db2_plan})
     PKLIST({package_list})
     OWNER({db2_owner})
     QUALIFIER({db2_owner})
     ACTION(REPLACE)
     ISOLATION(CS)
     RELEASE(COMMIT)
     VALIDATE(BIND)
     CURRENTDATA(NO)
     DYNAMICRULES(BIND)
     DEGREE(1)
     EXPLAIN(NO);
"""
    
    if not db2_utils.execute_sql(sql_bind_plan, verbose):
        print("✗ Failed to bind plan")
        return False
    
    print(f"✓ Plan {db2_plan} bound successfully")
    
    # Step 3: Grant execute on plan
    print_step(3, "Granting Execute Permissions")
    
    bank_user = config.get('BANK_USER')
    
    sql_grant = f"""
GRANT EXECUTE ON PLAN {db2_plan} TO {bank_user};
"""
    
    if not db2_utils.execute_sql(sql_grant, verbose):
        print("⚠ Warning: Failed to grant execute permission")
    else:
        print(f"✓ Execute permission granted to {bank_user}")
    
    return True


def rebind_db2_plan(config: BuildConfig, verbose: bool = False) -> bool:
    """Rebind existing DB2 plan"""
    
    print_banner("DB2 Plan Rebind")
    
    db2_utils = DB2Utilities(config)
    db2_plan = config.get('DB2_PLAN')
    
    sql_rebind = f"""
REBIND PLAN({db2_plan})
       ISOLATION(CS)
       CURRENTDATA(NO);
"""
    
    if db2_utils.execute_sql(sql_rebind, verbose):
        print(f"✓ Plan {db2_plan} rebound successfully")
        return True
    else:
        print(f"✗ Failed to rebind plan {db2_plan}")
        return False


def free_db2_plan(config: BuildConfig, verbose: bool = False) -> bool:
    """Free (drop) DB2 plan and packages"""
    
    print_banner("Freeing DB2 Plan and Packages")
    
    db2_utils = DB2Utilities(config)
    db2_plan = config.get('DB2_PLAN')
    db2_package = config.get('DB2_PACKAGE')
    
    # Free plan
    sql_free_plan = f"""
FREE PLAN({db2_plan});
"""
    
    if db2_utils.execute_sql(sql_free_plan, verbose):
        print(f"✓ Plan {db2_plan} freed")
    else:
        print(f"⚠ Could not free plan {db2_plan} (may not exist)")
    
    # Free packages
    sql_free_packages = f"""
FREE PACKAGE({db2_package}.*);
"""
    
    if db2_utils.execute_sql(sql_free_packages, verbose):
        print(f"✓ Packages {db2_package}.* freed")
    else:
        print(f"⚠ Could not free packages {db2_package}.* (may not exist)")
    
    return True


def main():
    """Main execution"""
    import argparse
    
    parser = argparse.ArgumentParser(description='Bind CBSA programs to DB2')
    parser.add_argument('-c', '--config', default='build.conf', help='Configuration file')
    parser.add_argument('-v', '--verbose', action='store_true', help='Verbose output')
    parser.add_argument('--rebind', action='store_true', help='Rebind existing plan')
    parser.add_argument('--free', action='store_true', help='Free (drop) plan and packages')
    
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
    
    # Free plan if requested
    if args.free:
        if not free_db2_plan(config, args.verbose):
            print("ERROR: Failed to free DB2 plan")
            return 1
        print("\n✓ DB2 plan and packages freed successfully!")
        return 0
    
    # Rebind if requested
    if args.rebind:
        if not rebind_db2_plan(config, args.verbose):
            print("ERROR: DB2 plan rebind failed")
            return 1
        print("\n✓ DB2 plan rebound successfully!")
        return 0
    
    # Normal bind
    if not bind_db2_plan(config, args.verbose):
        print("ERROR: DB2 binding failed")
        return 1
    
    print("\n✓ DB2 binding completed successfully!")
    return 0


if __name__ == '__main__':
    sys.exit(main())

# Made with Bob
