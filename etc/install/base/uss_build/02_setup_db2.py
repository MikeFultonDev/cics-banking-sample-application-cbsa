#!/usr/bin/env python3
"""
CBSA DB2 Setup Script
Equivalent to INSTDB2.jcl - Creates DB2 database, tables, and indexes
"""

import sys
import os
from cbsa_utils import BuildConfig, DB2Utilities, print_banner, print_step, check_prerequisites


def create_db2_artifacts(config: BuildConfig, verbose: bool = False) -> bool:
    """Create all DB2 artifacts for CBSA"""
    
    print_banner("CBSA DB2 Artifact Creation")
    
    db2_utils = DB2Utilities(config)
    db2_owner = config.get('DB2_OWNER')
    vcat = config.get('DB2_VCAT')
    
    # Step 1: Create Database
    print_step(1, "Creating CBSA Database")
    sql_create_db = f"""
SET CURRENT SQLID = '{db2_owner}';

CREATE DATABASE CBSA
       BUFFERPOOL BP1
       INDEXBP BP0;
"""
    
    if not db2_utils.execute_sql(sql_create_db, verbose):
        print("✗ Failed to create database")
        return False
    print("✓ Database created successfully")
    
    # Step 2: Create ACCOUNT storage group and tablespace
    print_step(2, "Creating ACCOUNT Storage Group and Tablespace")
    sql_account_sg = f"""
SET CURRENT SQLID = '{db2_owner}';

CREATE STOGROUP ACCOUNT VOLUMES('*','*','*','*','*') VCAT {vcat};

CREATE TABLESPACE ACCOUNT IN CBSA USING STOGROUP ACCOUNT;
"""
    
    if not db2_utils.execute_sql(sql_account_sg, verbose):
        print("✗ Failed to create ACCOUNT storage group/tablespace")
        return False
    print("✓ ACCOUNT storage group and tablespace created")
    
    # Step 3: Create ACCOUNT table
    print_step(3, "Creating ACCOUNT Table")
    sql_account_table = f"""
SET CURRENT SQLID = '{db2_owner}';

CREATE TABLE ACCOUNT (
                    ACCOUNT_EYECATCHER             CHAR(4),
                    ACCOUNT_CUSTOMER_NUMBER        CHAR(10),
                    ACCOUNT_SORTCODE               CHAR(6) NOT NULL,
                    ACCOUNT_NUMBER                 CHAR(8) NOT NULL,
                    ACCOUNT_TYPE                   CHAR(8),
                    ACCOUNT_INTEREST_RATE          DECIMAL(6, 2),
                    ACCOUNT_OPENED                 DATE,
                    ACCOUNT_OVERDRAFT_LIMIT        INTEGER,
                    ACCOUNT_LAST_STATEMENT         DATE,
                    ACCOUNT_NEXT_STATEMENT         DATE,
                    ACCOUNT_AVAILABLE_BALANCE      DECIMAL(12, 2),
                    ACCOUNT_ACTUAL_BALANCE         DECIMAL(12, 2)
                   )
IN CBSA.ACCOUNT   NOT VOLATILE
CARDINALITY  AUDIT NONE  DATA CAPTURE NONE;
"""
    
    if not db2_utils.execute_sql(sql_account_table, verbose):
        print("✗ Failed to create ACCOUNT table")
        return False
    print("✓ ACCOUNT table created")
    
    # Step 4: Create ACCOUNT indexes
    print_step(4, "Creating ACCOUNT Indexes")
    sql_account_indexes = f"""
SET CURRENT SQLID = '{db2_owner}';

CREATE UNIQUE INDEX ACCTINDX
  ON ACCOUNT(ACCOUNT_SORTCODE,ACCOUNT_NUMBER)
  USING STOGROUP ACCOUNT;

CREATE INDEX ACCTCUST
   ON ACCOUNT(ACCOUNT_SORTCODE,ACCOUNT_CUSTOMER_NUMBER)
   USING STOGROUP ACCOUNT;
"""
    
    if not db2_utils.execute_sql(sql_account_indexes, verbose):
        print("✗ Failed to create ACCOUNT indexes")
        return False
    print("✓ ACCOUNT indexes created")
    
    # Step 5: Create PROCTRAN storage group and tablespace
    print_step(5, "Creating PROCTRAN Storage Group and Tablespace")
    sql_proctran_sg = f"""
SET CURRENT SQLID = '{db2_owner}';

CREATE STOGROUP PROCTRAN VOLUMES('*','*','*','*','*') VCAT {vcat};

CREATE TABLESPACE PROCTRAN IN CBSA USING STOGROUP PROCTRAN;
"""
    
    if not db2_utils.execute_sql(sql_proctran_sg, verbose):
        print("✗ Failed to create PROCTRAN storage group/tablespace")
        return False
    print("✓ PROCTRAN storage group and tablespace created")
    
    # Step 6: Create PROCTRAN table
    print_step(6, "Creating PROCTRAN Table")
    sql_proctran_table = f"""
SET CURRENT SQLID = '{db2_owner}';

CREATE TABLE PROCTRAN
                  (
                    PROCTRAN_EYECATCHER            CHAR(4),
                    PROCTRAN_SORTCODE              CHAR(6) NOT NULL,
                    PROCTRAN_NUMBER                CHAR(8) NOT NULL,
                    PROCTRAN_DATE                  DATE,
                    PROCTRAN_TIME                  CHAR(6),
                    PROCTRAN_REF                   CHAR(12),
                    PROCTRAN_TYPE                  CHAR(3),
                    PROCTRAN_DESC                  CHAR(40),
                    PROCTRAN_AMOUNT                DECIMAL(12, 2)
                   )
IN CBSA.PROCTRAN  NOT VOLATILE
CARDINALITY  AUDIT NONE  DATA CAPTURE NONE;
"""
    
    if not db2_utils.execute_sql(sql_proctran_table, verbose):
        print("✗ Failed to create PROCTRAN table")
        return False
    print("✓ PROCTRAN table created")
    
    # Step 7: Create CONTROL storage group and tablespace
    print_step(7, "Creating CONTROL Storage Group and Tablespace")
    sql_control_sg = f"""
SET CURRENT SQLID = '{db2_owner}';

CREATE STOGROUP CONTROL VOLUMES('*','*','*','*','*') VCAT {vcat};

CREATE TABLESPACE CONTROL IN CBSA USING STOGROUP CONTROL;
"""
    
    if not db2_utils.execute_sql(sql_control_sg, verbose):
        print("✗ Failed to create CONTROL storage group/tablespace")
        return False
    print("✓ CONTROL storage group and tablespace created")
    
    # Step 8: Create CONTROL table
    print_step(8, "Creating CONTROL Table")
    sql_control_table = f"""
SET CURRENT SQLID = '{db2_owner}';

CREATE TABLE CONTROL (
                    CONTROL_NAME                   CHAR(32),
                    CONTROL_VALUE_NUM              INTEGER,
                    CONTROL_VALUE_STR              CHAR(40)
                   )
IN CBSA.CONTROL  NOT VOLATILE
CARDINALITY  AUDIT NONE  DATA CAPTURE NONE;
"""
    
    if not db2_utils.execute_sql(sql_control_table, verbose):
        print("✗ Failed to create CONTROL table")
        return False
    print("✓ CONTROL table created")
    
    # Step 9: Create CONTROL index
    print_step(9, "Creating CONTROL Index")
    sql_control_index = f"""
SET CURRENT SQLID = '{db2_owner}';

CREATE UNIQUE INDEX CONTINDX
 ON CONTROL(CONTROL_NAME)
 USING STOGROUP CONTROL;
"""
    
    if not db2_utils.execute_sql(sql_control_index, verbose):
        print("✗ Failed to create CONTROL index")
        return False
    print("✓ CONTROL index created")
    
    # Step 10: Grant permissions
    print_step(10, "Granting Permissions")
    bank_user = config.get('BANK_USER')
    sql_grants = f"""
SET CURRENT SQLID = '{db2_owner}';

GRANT ALL ON DATABASE CBSA TO {bank_user};
GRANT ALL ON TABLE ACCOUNT TO {bank_user};
GRANT ALL ON TABLE PROCTRAN TO {bank_user};
GRANT ALL ON TABLE CONTROL TO {bank_user};
"""
    
    if not db2_utils.execute_sql(sql_grants, verbose):
        print("⚠ Warning: Failed to grant permissions (may need manual intervention)")
    else:
        print("✓ Permissions granted")
    
    return True


def drop_db2_artifacts(config: BuildConfig, verbose: bool = False) -> bool:
    """Drop all DB2 artifacts (for cleanup/reinstall)"""
    
    print_banner("Dropping CBSA DB2 Artifacts")
    
    db2_utils = DB2Utilities(config)
    db2_owner = config.get('DB2_OWNER')
    
    sql_drop = f"""
SET CURRENT SQLID = '{db2_owner}';

DROP INDEX CONTINDX;
DROP TABLE CONTROL;
DROP TABLESPACE CBSA.CONTROL;
DROP STOGROUP CONTROL;

DROP TABLE PROCTRAN;
DROP TABLESPACE CBSA.PROCTRAN;
DROP STOGROUP PROCTRAN;

DROP INDEX ACCTCUST;
DROP INDEX ACCTINDX;
DROP TABLE ACCOUNT;
DROP TABLESPACE CBSA.ACCOUNT;
DROP STOGROUP ACCOUNT;

DROP DATABASE CBSA;
"""
    
    print("Dropping all CBSA DB2 objects...")
    if db2_utils.execute_sql(sql_drop, verbose):
        print("✓ DB2 artifacts dropped successfully")
        return True
    else:
        print("⚠ Some objects may not have been dropped (they may not exist)")
        return True  # Return True anyway as this is cleanup


def main():
    """Main execution"""
    import argparse
    
    parser = argparse.ArgumentParser(description='Setup CBSA DB2 artifacts')
    parser.add_argument('-c', '--config', default='build.conf', help='Configuration file')
    parser.add_argument('-v', '--verbose', action='store_true', help='Verbose output')
    parser.add_argument('--drop', action='store_true', help='Drop existing artifacts before creating')
    parser.add_argument('--drop-only', action='store_true', help='Only drop artifacts, do not create')
    
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
    
    # Drop existing artifacts if requested
    if args.drop or args.drop_only:
        if not drop_db2_artifacts(config, args.verbose):
            print("ERROR: Failed to drop DB2 artifacts")
            if not args.drop_only:
                return 1
    
    # Create artifacts unless drop-only
    if not args.drop_only:
        if not create_db2_artifacts(config, args.verbose):
            print("ERROR: DB2 artifact creation failed")
            return 1
    
    print("\n✓ DB2 setup completed successfully!")
    return 0


if __name__ == '__main__':
    sys.exit(main())

# Made with Bob
