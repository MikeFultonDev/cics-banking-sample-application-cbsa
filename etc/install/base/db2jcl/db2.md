# Db2 Assets Required by CICS Banking Sample Application

This document describes the Db2 assets needed by the CICS Banking Sample Application (CBSA) based on the JCL files in this directory.

## Database

**Database Name:** `CBSA`

- **Buffer Pool:** BP1
- **Index Buffer Pool:** BP0

## Storage Groups

The application requires three storage groups:

1. **ACCOUNT** - Storage group for account data
   - Volumes: 5 volumes ('*','*','*','*','*')
   - VCAT: DSNV12DP

2. **PROCTRAN** - Storage group for processed transactions
   - Volumes: 5 volumes ('*','*','*','*','*')
   - VCAT: DSNV12DP

3. **CONTROL** - Storage group for control data
   - Volumes: 5 volumes ('*','*','*','*','*')
   - VCAT: DSNV12DP

## Tablespaces

Three tablespaces are required within the CBSA database:

1. **ACCOUNT** - Uses STOGROUP ACCOUNT
2. **PROCTRAN** - Uses STOGROUP PROCTRAN
3. **CONTROL** - Uses STOGROUP CONTROL

## Tables

### 1. ACCOUNT Table

Located in tablespace `CBSA.ACCOUNT`

**Columns:**
- `ACCOUNT_EYECATCHER` - CHAR(4)
- `ACCOUNT_CUSTOMER_NUMBER` - CHAR(10)
- `ACCOUNT_SORTCODE` - CHAR(6) NOT NULL
- `ACCOUNT_NUMBER` - CHAR(8) NOT NULL
- `ACCOUNT_TYPE` - CHAR(8)
- `ACCOUNT_INTEREST_RATE` - DECIMAL(6, 2)
- `ACCOUNT_OPENED` - DATE
- `ACCOUNT_OVERDRAFT_LIMIT` - INTEGER
- `ACCOUNT_LAST_STATEMENT` - DATE
- `ACCOUNT_NEXT_STATEMENT` - DATE
- `ACCOUNT_AVAILABLE_BALANCE` - DECIMAL(12, 2)
- `ACCOUNT_ACTUAL_BALANCE` - DECIMAL(12, 2)

**Properties:**
- NOT VOLATILE
- CARDINALITY
- AUDIT NONE
- DATA CAPTURE NONE

### 2. PROCTRAN Table

Located in tablespace `CBSA.PROCTRAN`

**Columns:**
- `PROCTRAN_EYECATCHER` - CHAR(4)
- `PROCTRAN_SORTCODE` - CHAR(6) NOT NULL
- `PROCTRAN_NUMBER` - CHAR(8) NOT NULL
- `PROCTRAN_DATE` - DATE
- `PROCTRAN_TIME` - CHAR(6)
- `PROCTRAN_REF` - CHAR(12)
- `PROCTRAN_TYPE` - CHAR(3)
- `PROCTRAN_DESC` - CHAR(40)
- `PROCTRAN_AMOUNT` - DECIMAL(12, 2)

**Properties:**
- NOT VOLATILE
- CARDINALITY
- AUDIT NONE
- DATA CAPTURE NONE

### 3. CONTROL Table

Located in tablespace `CBSA.CONTROL`

**Columns:**
- `CONTROL_NAME` - CHAR(32)
- `CONTROL_VALUE_NUM` - INTEGER
- `CONTROL_VALUE_STR` - CHAR(40)

**Properties:**
- NOT VOLATILE
- CARDINALITY
- AUDIT NONE
- DATA CAPTURE NONE

## Indexes

### 1. ACCTINDX (Unique Index)

- **Table:** ACCOUNT
- **Columns:** ACCOUNT_SORTCODE, ACCOUNT_NUMBER
- **Type:** UNIQUE
- **Storage:** Uses STOGROUP ACCOUNT

### 2. ACCTCUST (Non-unique Index)

- **Table:** ACCOUNT
- **Columns:** ACCOUNT_SORTCODE, ACCOUNT_CUSTOMER_NUMBER
- **Storage:** Uses STOGROUP ACCOUNT

### 3. CONTINDX (Unique Index)

- **Table:** CONTROL
- **Columns:** CONTROL_NAME
- **Type:** UNIQUE
- **Storage:** Uses STOGROUP CONTROL

## Db2 Packages

The application requires the following Db2 packages to be bound:

1. **CREACC** - Create Account
2. **CRECUST** - Create Customer
3. **DBCRFUN** - Database Credit Function
4. **DELACC** - Delete Account
5. **DELCUS** - Delete Customer
6. **INQACC** - Inquire Account
7. **INQACCCU** - Inquire Account by Customer
8. **BANKDATA** - Bank Data
9. **UPDACC** - Update Account
10. **XFRFUN** - Transfer Function

All packages are bound with:
- **Owner:** Specified by `&DB2OWNER` variable
- **Qualifier:** Specified by `&DB2OWNER` variable
- **Action:** REPLACE

## Db2 Plan

**Plan Name:** Specified by `&BANKPLAN` variable

**Configuration:**
- **Owner:** Specified by `&DB2OWNER` variable
- **Isolation Level:** UR (Uncommitted Read)
- **Package List:** NULLID.*, &BANKPKGE..*

## Security and Grants

The application requires the following grants:

### Plan Execution
- `GRANT EXECUTE ON PLAN &BANKPLAN TO &BANKUSER`

### Table Permissions
- `GRANT SELECT, INSERT, UPDATE, DELETE ON TABLE &DB2OWNER..ACCOUNT TO &BANKUSER`
- `GRANT SELECT, INSERT, UPDATE, DELETE ON TABLE &DB2OWNER..PROCTRAN TO &BANKUSER`
- `GRANT SELECT, INSERT, UPDATE, DELETE ON TABLE &DB2OWNER..CONTROL TO &BANKUSER`

## Configuration Variables

The following variables must be configured in the DEFAULT.jcl member:

- **DB2HLQ** - High level qualifiers of DB2 datasets (SDSNLOAD, etc.)
- **DB2SYS** - DB2 subsystem name
- **DB2OWNER** - Userid that will own the DB2 resources
- **BANKDBRM** - Name of the DBRMLIB for the banking application
- **BANKPLAN** - DB2 plan name (must match CSD and Db2 Install job)
- **BANKPKGE** - Package name in DB2
- **DSNTEPP** - Plan name for DSNTEP2 utility program
- **DSNTEPL** - Load library containing DSNTEP2 utility program
- **BANKUSER** - Userid that will run the application (e.g., CICSUSER)

## Installation Order

Based on the JCL files, the recommended installation order is:

1. Create Database (CREDB00.jcl or use INSTDB2.jcl for complete setup)
2. Create Storage Groups (CRESG01.jcl, CRESG02.jcl, CRESG03.jcl)
3. Create Tablespaces (CRETS01.jcl, CRETS02.jcl, CRETS03.jcl)
4. Create Tables (CRETB01.jcl, CRETB02.jcl, CRETB03.jcl)
5. Create Indexes (CREI101.jcl, CREI201.jcl, CREI301.jcl)
6. Bind Packages and Plan (DB2BIND.jcl)

Alternatively, use **INSTDB2.jcl** which performs all creation steps in a single job.

## Cleanup

To remove all Db2 assets, use **DROPDB2.jcl** which drops all objects in reverse order.

## Notes

- The VCAT name (DSNV12DP) should be changed to match your installation's integrated catalog facility catalog
- All JCL files use symbolic parameters that must be customized for your environment
- The BTCHSQL.jcl file is provided for testing SQL queries against the database