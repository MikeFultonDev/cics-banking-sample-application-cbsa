# DB2 Grant Scripts

## Overview

This directory contains SQL scripts and templates to grant necessary Db2 privileges to users for CBSA database administration and operations.

## Required Privileges

The [`access.sql`](access.sql:1) script grants comprehensive system and database privileges:

```sql
GRANT CREATEDB ON SYSTEM TO '${DB2_OWNER}';
GRANT CREATEDBA ON SYSTEM TO '${DB2_OWNER}';
GRANT CREATEDBC ON SYSTEM TO '${DB2_OWNER}';
GRANT CREATESG ON SYSTEM TO '${DB2_OWNER}';
GRANT BINDADD ON SYSTEM TO '${DB2_OWNER}';
GRANT DBADM ON DATABASE CBSA TO '${DB2_OWNER}';
GRANT USE OF BUFFERPOOL BP1 TO '${DB2_OWNER}';
GRANT USE OF BUFFERPOOL BP2 TO '${DB2_OWNER}';
```

These grants enable:
- **CREATEDB** - Create databases
- **CREATEDBA/CREATEDBC** - Create database aliases and connections
- **CREATESG** - Create storage groups
- **BINDADD** - Bind packages and plans
- **DBADM** - Full database administration on CBSA database
- **USE OF BUFFERPOOL** - Use BP1 and BP2 buffer pools

## Usage with batchtsocmd

Use [`batchtsocmd`](https://pypi.org/project/batchtsocmd/) (version 0.1.9+) to execute the grants:

```bash
# Set environment variables
export DB2_SUBSYSTEM=DBD1
export DB2_OWNER=FULTONM
export DB2_DSNTIAD_PLAN=DSNTIAD
export DB2_SUBSYSTEM_LOADLIB=DBD1.RUNLIB.LOAD

# Generate files using envsubst
envsubst < systsin.template > /tmp/grant.systsin
envsubst < access.sql > /tmp/grant.sql

# Execute with batchtsocmd
batchtsocmd --systsin /tmp/grant.systsin \
            --sysin /tmp/grant.sql \
            --steplib DBD1.SDSNLOAD
```

## Important Notes

1. **DSNTIAD Required**: These grants use DSNTIAD (not DSNTEP2) because GRANT statements are DCL (Data Control Language) commands that require write access.

2. **SYSADM Authority**: The user executing these grants must have SYSADM or appropriate authority in Db2.

3. **Plan Binding**: If DSNTIAD plan is not bound or authorized, you may need to:
   - Use SPUFI (TSO ISPF → DB2I → SPUFI)
   - Have a Db2 administrator execute the grants
   - Bind the DSNTIAD plan first

4. **Variable Substitution**: The `${DB2_OWNER}` variable is replaced by `envsubst` before execution.

## Alternative: Using SPUFI

If batchtsocmd is unavailable or DSNTIAD plan issues occur:

1. TSO ISPF → **Option D** (DB2I)
2. **Option 1** (SPUFI)
3. Enter SQL directly (replace `${DB2_OWNER}` with actual username)
4. Execute

## See Also

- [`systsin.template`](systsin.template:1) - TSO SYSTSIN template for DSNTIAD
- [`access.sql`](access.sql:1) - SQL grant statements
- [`../db2.mk`](../db2.mk:1) - Makefile with grant automation
- [`../requirements.txt`](../requirements.txt:1) - Python dependencies including batchtsocmd
