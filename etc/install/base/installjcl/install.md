# CICS Banking Sample Application - Installation JCL Assets

This document describes the assets managed by the JCL files in the installjcl directory.

## Build Approaches

There are two approaches to building and installing the CICS Banking Sample Application:

### 1. Traditional JCL Build (Original Method)
Uses JCL jobs to create all datasets, copy source files from PDSs, compile, and link-edit programs. This approach requires all source files to be uploaded to MVS datasets first.

### 2. USS Build with Makefiles (Modern Method)
Uses the `uss_build` directory with Python scripts and makefiles to build directly from the USS file system after a git clone. This approach is more efficient and modern.

**Key Difference**: When using the USS build approach, you do NOT need to create source code datasets (COBOL, BMS, ASM, COPYLIB, DSECT) because the build process reads directly from the USS file system. You only need to create the target/output datasets.

## Required Datasets for USS Build Method

When using the `uss_build` directory and makefiles, you only need to create these datasets:

### Essential Datasets (Required):
1. **LOADLIB** (CREL003.jcl) - Stores compiled load modules
2. **DBRM** (CREL004.jcl) - Stores Database Request Modules for DB2
3. **VSAM files** (BANKDATA.jcl) - Customer and abend data files

### Optional Datasets (May be needed depending on your build process):
4. **LKED** (CREL005.jcl) - Link-edit JCL (if using JCL for link-edit)
5. **CBSAMOD** (CREL008.jcl) - CBSA modules (if needed for intermediate objects)

### NOT Required for USS Build:
- ~~BUILDJCL (CREL001.jcl)~~ - Not needed, using makefiles instead
- ~~COPYLIB (CREL002.jcl)~~ - Not needed, using files from `src/base/cobol_copy/`
- ~~BMS (CREL006.jcl)~~ - Not needed, using files from `src/base/bms_src/`
- ~~ASM (CREL007.jcl)~~ - Not needed, using files from USS if any assembler code exists
- ~~COBOL (CREL009.jcl)~~ - Not needed, using files from `src/base/cobol_src/`
- ~~DSECT (CREL010.jcl)~~ - Not needed, using files from USS
- ~~REORG (CREL011.jcl)~~ - Not needed for initial build
- ~~DB2.JCL.INSTALL (CREDB2L.jcl)~~ - Not needed, using Python scripts instead


## Library Creation Jobs

### CRELIBS.jcl
Master job that includes all library creation jobs to create the complete set of CBSA datasets.

### CREDB2L.jcl
Creates DB2-related JCL installation library:
- **Dataset**: `&HLQ..DB2.JCL.INSTALL`
- **Type**: PDSE
- **Space**: 2 cylinders (primary), 1 cylinder (secondary)
- **Purpose**: Stores DB2 installation JCL members

### CREL001.jcl
Creates build JCL library:
- **Dataset**: `&HLQ..CICSBSA.BUILDJCL`
- **Type**: PDSE
- **Space**: 5 cylinders (primary), 1 cylinder (secondary)
- **Purpose**: Stores build job control language

### CREL002.jcl
Creates COBOL copybook library:
- **Dataset**: `&HLQ..CICSBSA.COPYLIB`
- **Type**: PDSE
- **Space**: 5 cylinders (primary), 1 cylinder (secondary)
- **Purpose**: Stores COBOL copybooks and include files

### CREL003.jcl
Creates load module library:
- **Dataset**: `&HLQ..CICSBSA.LOADLIB`
- **Type**: PDSE (load library format)
- **Space**: 5 cylinders (primary), 1 cylinder (secondary)
- **Purpose**: Stores compiled and linked executable programs

### CREL004.jcl
Creates DBRM library:
- **Dataset**: `&HLQ..CICSBSA.DBRM`
- **Type**: PDSE
- **Space**: 30 cylinders (primary), 20 cylinders (secondary)
- **Purpose**: Stores Database Request Modules for DB2 programs

### CREL005.jcl
Creates link-edit JCL library:
- **Dataset**: `&HLQ..CICSBSA.LKED`
- **Type**: PDSE
- **Space**: 1 cylinder (primary), 2 cylinders (secondary)
- **Purpose**: Stores link-edit job control language

### CREL006.jcl
Creates BMS map library:
- **Dataset**: `&HLQ..CICSBSA.BMS`
- **Type**: PDSE
- **Space**: 5 cylinders (primary), 2 cylinders (secondary)
- **Purpose**: Stores Basic Mapping Support (BMS) map definitions

### CREL007.jcl
Creates assembler source library:
- **Dataset**: `&HLQ..CICSBSA.ASM`
- **Type**: PDSE
- **Space**: 3 cylinders (primary), 2 cylinders (secondary)
- **Purpose**: Stores assembler language source code

### CREL008.jcl
Creates CBSA module library:
- **Dataset**: `&HLQ..CICSBSA.CBSAMOD`
- **Type**: PDSE
- **Space**: 50 cylinders (primary), 20 cylinders (secondary)
- **Purpose**: Stores CBSA-specific modules

### CREL009.jcl
Creates COBOL source library:
- **Dataset**: `&HLQ..CICSBSA.COBOL`
- **Type**: PDSE
- **Space**: 7 cylinders (primary), 5 cylinders (secondary)
- **Purpose**: Stores COBOL source programs

### CREL010.jcl
Creates DSECT library:
- **Dataset**: `&HLQ..CICSBSA.DSECT`
- **Type**: PDSE
- **Space**: 5 cylinders (primary), 1 cylinder (secondary)
- **Purpose**: Stores data structure definitions (DSECTs)

### CREL011.jcl
Creates reorganization library:
- **Dataset**: `&HLQ..CICSBSA.REORG`
- **Type**: PDSE
- **Space**: 5 cylinders (primary), 1 cylinder (secondary)
- **Purpose**: Stores reorganization utilities and scripts

## VSAM Data Files

### BANKDATA.jcl
Creates and populates VSAM files for the banking application:

#### VSAM Clusters Created:
1. **ABNDFILE** - Abend tracking file
   - **Dataset**: `@BANK_PREFIX@.ABNDFILE`
   - **Type**: KSDS (Key-Sequenced Data Set)
   - **Space**: 6 cylinders (primary), 6 cylinders (secondary)
   - **Key**: 12 bytes at offset 0
   - **Record Size**: 681 bytes (fixed)
   - **Purpose**: Tracks application abends and errors

2. **CUSTOMER** - Customer master file
   - **Dataset**: `@BANK_PREFIX@.CUSTOMER`
   - **Type**: KSDS (Key-Sequenced Data Set)
   - **Space**: 50 cylinders (primary), 50 cylinders (secondary)
   - **Key**: 16 bytes at offset 4
   - **Record Size**: 259 bytes (fixed)
   - **Purpose**: Stores customer information
   - **Logging**: UNDO logging enabled

#### Data Population:
- Executes COBOL program **BANKDATA** to generate random customer data
- Parameters:
  - Starting Customer Number: 1
  - Final Customer Number: 10000
  - Customer Number Increment: 1
  - Random seed: 1000000000000000
- Uses DB2 plan: `@DB2_PLAN@` (CBSA)
- DB2 subsystem: `@DB2_SUBSYSTEM@` (DBCG)

## CICS Configuration

### CBSACSD.jcl
Updates CICS System Definition (CSD):
- **Program**: DFHCSDUP
- **CSD Dataset**: `@CSD_PREFIX@.DFHCSD` (CBSA.CICSREG.DFHCSD)
- **Input**: BANK member from `@CBSA_INSTALL@` PDS
- **Purpose**: Defines CICS resources for the banking application

### CICSTS56.jcl
CICS TS 5.6 startup procedure:
- **Region**: CICSTS56
- **APPLID**: CICSTS56
- **SIT**: 6$
- **SYSIDNT**: S730

#### Key Datasets Referenced:
- **DFHCSD**: CICS System Definition
- **DFHTEMP**: Auxiliary temporary storage
- **DFHINTRA**: Intrapartition dataset
- **DFHAUXT/DFHBUXT**: Auxiliary trace datasets
- **DFHLCD**: Local catalog
- **DFHGCD**: Global catalog
- **DFHLRQ**: Local request queue
- **DFHDMPA/DFHDMPB**: Dump datasets
- **FILEA**: Sample VSAM file

#### Load Libraries:
- `CBSA.CICSBSA.LOADLIB` - Banking application load library
- CICS system libraries (SDFHLOAD, SDFHAUTH, SEYULOAD, SEYUAUTH)
- DB2 libraries (SDSNLOAD, SDSNLOD2)
- Language Environment (SCEERUN, SCEERUN2, SCEECICS)
- TCP/IP support (SEZATCP)

#### Features Enabled:
- DB2 connectivity (DB2CONN=YES)
- TCP/IP services (TCPIP=YES)
- FEPI interface (FEPI=YES)
- Security (SEC=YES)
- RACF keyring: CICSRNG

### DFH$SIP1.jcl
CICS System Initialization Parameters:
- **APPLID**: CICSTS56
- **DB2CONN**: YES
- **GRPLIST**: XYZLIST, CICSTS56
- **GMTRAN**: CESN (good morning transaction)
- **Security**: Enabled with various transaction/command security options
- **JVM Profile Directory**: `/var/cics/JVMProfiles/`
- **USS Home**: `/usr/lpp/cicsts/cicsts56`

## Security Configuration

### RACF001.jcl
Defines RACF security profiles for DB2 access:
- **Profile 1**: `DFHDB2.AUTHTYPE.HBANK`
  - Permits READ access to: CICSUSER, IBMUSER, JCOLLET, OGRADYJ
- **Profile 2**: `DFHDB2.AUTHTYPE.DBCG`
  - Permits READ access to: CICSUSER, IBMUSER, JCOLLET, OGRADYJ
- **Class**: FACILITY
- Refreshes RACLIST after updates

## Deployment Jobs

### REPLCICS.jcl
Replaces CICS startup procedure:
- **Source**: `CBSA.JCL.INSTALL(CICSTS56)`
- **Target**: `FEU.Z25A.PROCLIB(CICSTS56)`
- **Purpose**: Deploys CICS startup JCL to system PROCLIB

### REPLSIP.jcl
Replaces CICS SIP member:
- **Source**: `CBSA.JCL.INSTALL(DFH$SIP1)`
- **Target**: `DFH560.SYSIN(DFH$SIP1)`
- **Purpose**: Deploys CICS system initialization parameters

## Operational Jobs

### RESTCICS.jcl
Restarts CICS region:
- **Command**: `S CICSTS56`
- **Purpose**: Starts the CICSTS56 CICS region

### RESTZOSC.jcl
Restarts z/OS Connect server:
- **Command**: `S ZOSCSRV`
- **Purpose**: Starts the z/OS Connect server

### SHUTCICS.jcl
Shuts down CICS region:
- **Command**: `C CICSTS56`
- **Purpose**: Stops the CICSTS56 CICS region

### SHUTZOSC.jcl
Shuts down z/OS Connect server:
- **Command**: `C ZOSCSRV`
- **Purpose**: Stops the z/OS Connect server

### ZOSCSEC.jcl
Sets z/OS Connect security permissions:
- **Command**: `chmod -R g+rwx` on z/OS Connect resources directory
- **Path**: `/var/zosconnect/v3r0/servers/defaultServer/resources/zosconnect`
- **Purpose**: Ensures proper group permissions for z/OS Connect resources

## Additional Assets

### BANK.csd
CICS System Definition input file containing resource definitions for the banking application.

### README.md
Documentation file for the installjcl directory.

## Variable Substitution

The JCL files use the following symbolic parameters that must be replaced before execution:

- `&HLQ` or `@BANK_PREFIX@`: High-level qualifier (typically `CBSA.CICSBSA`)
- `@CICS_PREFIX@`: CICS installation prefix (typically `DFH560.CICS`)
- `@CSD_PREFIX@`: CSD dataset prefix (typically `CBSA.CICSREG`)
- `@DB2_HLQ@`: DB2 high-level qualifier (typically `DSNC10`)
- `@DB2_SUBSYSTEM@`: DB2 subsystem name (typically `DBCG`)
- `@DB2_PLAN@`: DB2 plan name (typically `CBSA`)
- `@BANK_LOADLIB@`: Load library name (typically `CBSA.CICSBSA.LOADLIB`)
- `@BANK_DBRMLIB@`: DBRM library name (typically `CBSA.CICSBSA.DBRM`)
- `@CBSA_INSTALL@`: Installation PDS name

## Installation Sequence

### Traditional JCL Build Method:
1. Run `CRELIBS.jcl` to create all required libraries
2. Upload source files to the created datasets
3. Run build JCL jobs to compile and link programs
4. Run `BANKDATA.jcl` to create VSAM files and populate customer data
5. Run `CBSACSD.jcl` to define CICS resources
6. Run `RACF001.jcl` to set up security profiles
7. Run `REPLCICS.jcl` and `REPLSIP.jcl` to deploy CICS configuration
8. Run `RESTCICS.jcl` to start CICS
9. Run `RESTZOSC.jcl` to start z/OS Connect (if needed)

### USS Build Method (Recommended):
1. Clone the repository to USS: `git clone <repository-url>`
2. Create only the required datasets:
   - Run `CREL003.jcl` to create LOADLIB
   - Run `CREL004.jcl` to create DBRM library
   - Run `BANKDATA.jcl` to create VSAM files (without data population step)
3. Navigate to `etc/install/base/uss_build/` directory
4. Run Python scripts in sequence:
   - `01_create_libraries.py` - Creates any additional required datasets
   - `02_setup_db2.py` - Sets up DB2 tables and data
   - Build scripts using makefiles to compile from USS
   - `05_populate_data.py` - Populates VSAM files with customer data
5. Run `CBSACSD.jcl` to define CICS resources
6. Run `RACF001.jcl` to set up security profiles
7. Run `REPLCICS.jcl` and `REPLSIP.jcl` to deploy CICS configuration
8. Run `RESTCICS.jcl` to start CICS
9. Run `RESTZOSC.jcl` to start z/OS Connect (if needed)

**Note**: The USS build method is more efficient as it eliminates the need to upload source files to MVS datasets and allows direct compilation from the USS file system.