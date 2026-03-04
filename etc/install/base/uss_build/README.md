# CBSA USS Build System

## Overview

This directory contains a modern build system for the CICS Banking Sample Application (CBSA) that runs in the z/OS UNIX System Services (USS) environment. It replaces the traditional JCL-based build process with GNU Make and includes both Python scripts for orchestration and a dedicated Makefile for COBOL compilation.

## Features

- **Makefile-based compilation**: Native incremental compilation with dependency tracking
- **USS-native builds**: All source and object files remain in USS (no MVS datasets required for compilation)
- **GNU Make orchestration**: Simple command-line interface for build tasks
- **Parallel compilation**: Built-in parallel execution for faster builds (`make -j4`)
- **Incremental builds**: Automatically rebuild only changed files
- **Modular design**: Separate Makefiles for compilation and orchestration
- **Configuration-driven**: Single configuration file for all settings
- **Error handling**: Better error reporting and recovery
- **Python automation**: Scripts for DB2, VSAM, and library management

## Prerequisites

- z/OS UNIX System Services (USS) environment
- Python 3.12 or later
- GNU Make
- Access to TSO commands (`tsocmd`)
- CICS TS 6.1 or greater
- DB2 v12 or greater
- z/OS Connect server (for REST APIs)
- Appropriate RACF permissions

### Python Dependencies

Install required Python packages:

```bash
pip install -r requirements.txt
```

This will install:
- `batchtsocmd` - For executing TSO commands in batch mode (published package from PyPI)
  - Note: `batchtsocmd` automatically installs `zos-ccsid-converter` as a dependency for EBCDIC/ASCII conversion
- Other dependencies as needed

**Note**: The `zoautil_py` package is typically pre-installed on z/OS systems. If not available, contact your system administrator.

## Directory Structure

```
uss_build/
├── README.md                    # This file
├── requirements.txt             # Python package dependencies
├── build.conf                   # Configuration file
├── Makefile                     # Main build orchestration
├── compile.mk                   # COBOL compilation Makefile
├── assemble.mk                  # BMS map assembly Makefile
├── db2.mk                       # DB2 management Makefile
├── scripts/                     # Python and bash scripts
│   ├── cbsa_utils.py           # Common utility functions
│   ├── cics_create.py          # CICS dataset creation and configuration
│   ├── populate_data.py        # Create VSAM files and populate data
│   ├── cobcc                   # COBOL compiler wrapper (bash)
│   ├── db2subst                # DB2 variable substitution (Python)
│   ├── envsubst                # Environment variable substitution (Python)
│   └── ldc                     # Link editor wrapper (bash)
├── bin/                         # Documentation for converters
├── db2grant/                    # DB2 grant scripts
├── db2sql/                      # DB2 SQL scripts
├── zos_ebcdic_converter/       # Local EBCDIC converter (legacy)
└── build/                       # Build output directory (created automatically)
    ├── obj/                     # Object files (.o)
    ├── load/                    # Load modules (executables)
    ├── dbrm/                    # DB2 Database Request Modules
    └── bmsmacro/                # BMS copybook macros
```

**Note**: The build system uses native Makefiles for compilation and binding:
- [`compile.mk`](compile.mk:1) - Incremental COBOL compilation with dependency tracking
- [`bind.mk`](bind.mk:1) - Incremental DB2 binding with DBRM dependencies

## Quick Start

### 1. Set Up Environment

**IMPORTANT**: Before running any build commands, you must source the `setenv` script to configure the Python environment:

```bash
# Set CBSADIR to the project root directory
export CBSADIR=/path/to/cics-banking-sample-application-cbsa

# Source the environment setup script
source ${CBSADIR}/setenv
```

The `setenv` script will:
- Configure the Python environment and PYTHONPATH
- Check for required Python packages (batchtsocmd, zoautil_py)
- Display warnings if any dependencies are missing
- Load host-specific configuration if available

If you see warnings about missing packages, install them:

```bash
pip install -r ${CBSADIR}/etc/install/base/uss_build/requirements.txt
```

### 2. Configure the Build

Edit [`build.conf`](build.conf:1) to match your environment:

```bash
# Edit configuration
vi build.conf
```

Key settings to update:
- `DB2_SYSTEM`: Your DB2 subsystem name (e.g., `DBCG`)
- `DB2_OWNER`: DB2 owner/qualifier (e.g., `IBMUSER`)
- `CICS_HLQ`: CICS high-level qualifier (e.g., `DFH560.CICS`)
- `ZOSCONNECT_*`: z/OS Connect paths and ports

### 3. Make Scripts Executable

```bash
make setup-scripts
```

### 4. Run Complete Installation

```bash
make install
```

This will execute all build steps in order:
1. Create MVS libraries
2. Setup DB2 database and tables
3. Compile COBOL programs and BMS maps
4. Bind programs to DB2
5. Create VSAM files and populate data
6. Verify installation

### 4. Verify Installation

```bash
make verify
```

## Makefile Targets

### Main Targets

| Target | Description |
|--------|-------------|
| `make help` | Display help information |
| `make install` | Complete installation (all steps) |
| `make verify` | Verify installation |
| `make clean` | Clean build artifacts |
| `make status` | Show build system status |

### Individual Build Steps

| Target | Description |
|--------|-------------|
| `make create-libs` | Create MVS libraries and copy source files |
| `make setup-db2` | Create DB2 database, tables, and indexes |
| `make compile` | Compile COBOL programs and assemble BMS maps |
| `make compile-programs` | Compile COBOL programs only |
| `make compile-maps` | Assemble BMS maps only |
| `make bind` | Bind programs to DB2 (packages and plan) |
| `make bind-packages` | Bind DB2 packages only |
| `make bind-plan` | Bind DB2 plan only |
| `make rebind-plan` | Rebind existing DB2 plan (faster) |
| `make populate` | Create VSAM files and populate data |

### Incremental Compilation and Binding

The new Makefile-based system supports true incremental compilation and binding:

| Target | Description |
|--------|-------------|
| `make build/load/CREACC` | Compile only the CREACC program |
| `make build/bind/CREACC.pkg` | Bind only the CREACC package |
| `make -j4 compile` | Compile with 4 parallel jobs |
| `make -f compile.mk help` | Show compilation-specific help |
| `make -f bind.mk help-bind` | Show binding-specific help |
| `make -f compile.mk list-programs` | List all programs |
| `make -f bind.mk list-db2-programs` | List DB2 programs |

### Advanced Targets

| Target | Description |
|--------|-------------|
| `make quick-install` | Install without data population |
| `make rebuild-db2` | Drop and recreate DB2 artifacts |
| `make rebuild-compile` | Recompile and rebind |
| `make clean-all` | Clean everything (DB2, VSAM, etc.) |

### Development Targets

| Target | Description |
|--------|-------------|
| `make dev-compile` | Compile programs only (skip maps) |
| `make dev-maps` | Compile maps only (skip programs) |
| `make compile-program PROGRAM=<name>` | Compile single program |

## Compilation System

### compile.mk - Native Makefile Compilation

The [`compile.mk`](compile.mk:1) file provides native GNU Make-based compilation with the following features:

**Key Features:**
- **Incremental compilation**: Only recompiles changed source files
- **Dependency tracking**: Automatically handles copybook dependencies
- **Parallel builds**: Use `make -j<N>` for parallel compilation
- **USS-native**: All files remain in USS (no MVS dataset copying)
- **Automatic directories**: Creates build directories as needed

**Usage Examples:**

```bash
# Compile everything
make compile

# Compile with 4 parallel jobs
make -j4 compile

# Compile single program (incremental)
make build/load/CREACC

# Compile programs only
make compile-programs

# Compile maps only
make compile-maps

# Clean and rebuild
make clean compile

# Show compilation help
make -f compile.mk help

# List all programs
make -f compile.mk list-programs

# Show build status
make -f compile.mk status
```

**Build Output:**
- Object files: `build/obj/*.o`
- Load modules: `build/load/*`
- DBRMs: `build/dbrm/*.dbrm`
- BMS DSECTs: `build/dsect/*.cpy`

**Dependency Tracking:**

The Makefile automatically tracks dependencies:
- Programs depend on their source files
- Programs depend on copybooks they include
- Programs depend on BMS DSECTs they use
- Only changed files are recompiled

**Example Workflow:**

```bash
# Initial compilation
make compile
# ✓ Compiles all 29 programs and 9 maps

# Edit CREACC.cbl
vi ../../../src/base/cobol_src/CREACC.cbl

# Incremental recompilation
make compile
# ✓ Only recompiles CREACC (much faster!)

# Edit a copybook
vi ../../../src/base/cobol_copy/CREACC.cpy

# Automatic dependency rebuild
make compile
# ✓ Recompiles CREACC and any other programs using CREACC.cpy
```

## Python Scripts

### 01_create_libraries.py

Creates MVS libraries (PDSEs) and copies source files from USS to MVS datasets.

**Usage:**
```bash
python3 01_create_libraries.py [options]

Options:
  -c, --config FILE     Configuration file (default: build.conf)
  -v, --verbose         Verbose output
  --skip-copy          Skip copying source files
  --copy-only          Only copy files, skip library creation
```

**Example:**
```bash
# Create libraries with verbose output
python3 01_create_libraries.py -v

# Only copy source files
python3 01_create_libraries.py --copy-only
```

### 02_setup_db2.py

Creates DB2 database, storage groups, tablespaces, tables, and indexes.

**Usage:**
```bash
python3 02_setup_db2.py [options]

Options:
  -c, --config FILE     Configuration file (default: build.conf)
  -v, --verbose         Verbose output
  --drop               Drop existing artifacts before creating
  --drop-only          Only drop artifacts, do not create
```

**Example:**
```bash
# Setup DB2 with verbose output
python3 02_setup_db2.py -v

# Recreate DB2 artifacts
python3 02_setup_db2.py --drop
```

### 03_compile_programs.py (DEPRECATED)

**Note**: This script is deprecated in favor of the native Makefile compilation system ([`compile.mk`](compile.mk:1)). It is retained for backward compatibility only.

The new Makefile-based system provides:
- True incremental compilation
- Better dependency tracking
- Native parallel execution
- Faster builds
- USS-native operation

**Migration:**
- Old: `python3 03_compile_programs.py -j 4`
- New: `make -j4 compile`

- Old: `python3 03_compile_programs.py --program CREACC`
- New: `make build/load/CREACC`

- Old: `python3 03_compile_programs.py --programs-only`
- New: `make compile-programs`

### 04_bind_db2.py

Binds COBOL programs to DB2 (creates packages and plan).

**Usage:**
```bash
python3 04_bind_db2.py [options]

Options:
  -c, --config FILE     Configuration file (default: build.conf)
  -v, --verbose         Verbose output
  --rebind             Rebind existing plan
  --free               Free (drop) plan and packages
```

**Example:**
```bash
# Bind programs to DB2
python3 04_bind_db2.py -v

# Rebind existing plan
python3 04_bind_db2.py --rebind
```
### populate_data.py


Creates VSAM files and populates DB2 tables with test data.

**Usage:**
```bash
python3 scripts/populate_data.py [options]

Options:
  -c, --config FILE     Configuration file (default: build.conf)
  -v, --verbose         Verbose output
  --start N            Starting customer number (default: 1)
  --end N              Ending customer number (default: 10000)
  --increment N        Customer number increment (default: 1)
  --seed N             Random seed (default: 1000000000000000)
  --skip-vsam          Skip VSAM file creation
  --skip-populate      Skip data population
  --verify-only        Only verify data, skip creation
```

**Example:**
```bash
# Populate with default data
python3 scripts/populate_data.py -v

# Populate with custom range
python3 scripts/populate_data.py --start 1 --end 5000

# Verify data only
python3 scripts/populate_data.py --verify-only
```

## Configuration File

The [`build.conf`](build.conf:1) file contains all environment-specific settings. Key sections:

### High Level Qualifiers
```bash
HLQ=CBSA
BANK_PREFIX=${HLQ}.CICSBSA
```

### CICS Configuration
```bash
CICS_HLQ=DFH560.CICS
CICS_REGION=CICSCBSA
```

### DB2 Configuration
```bash
DB2_HLQ=DSNC10
DB2_SYSTEM=DBCG
DB2_OWNER=IBMUSER
CBSA_PLAN=CBSA
CBSA_PACKAGE=PCBSA
```

### z/OS Connect Configuration
```bash
ZOSCONNECT_APIS=/var/zosconnect/v3r0/servers/defaultServer/resources/zosconnect/apis
ZOSCONNECT_SERVICES=/var/zosconnect/v3r0/servers/defaultServer/resources/zosconnect/services
ZOSCONNECT_HTTP_PORT=30701
ZOSCONNECT_HTTPS_PORT=30702
```

## Common Workflows

### Initial Installation

```bash
# 1. Configure
vi build.conf

# 2. Make scripts executable
make setup-scripts

# 3. Run full installation
make install

# 4. Verify
make verify
```

### Incremental Development Workflow

```bash
# 1. Edit a COBOL program
vi ../../../src/base/cobol_src/CREACC.cbl

# 2. Incremental recompile (only CREACC)
make build/load/CREACC

# 3. Rebind to DB2
make bind

# 4. Test changes
```

### Parallel Compilation

```bash
# Compile with 4 parallel jobs (much faster)
make -j4 compile

# Or specify more jobs for faster builds
make -j8 compile
```

### Rebuild After Code Changes

```bash
# Incremental rebuild (only changed files)
make compile

# Full rebuild
make clean compile

# Recompile and rebind
make rebuild-compile
```

### Recreate DB2 Artifacts

```bash
# Drop and recreate DB2
make rebuild-db2
```

### Clean and Reinstall

```bash
# Clean everything
make clean-all

# Reinstall
make install
```

## Troubleshooting

### Common Issues

**1. "tsocmd not found"**
- Ensure you're running in z/OS USS environment
- Check that TSO commands are in your PATH

**2. "Permission denied" errors**
- Verify RACF permissions for datasets and DB2
- Check file permissions on Python scripts (`chmod +x *.py`)

**3. Compilation failures**
- Check COBOL compiler (`COBCC`) is available
- Verify copybook paths in configuration
- Check build directory permissions
- Review compilation output in terminal
- Use verbose mode: `make compile VERBOSE=1`
- Check individual program: `make build/load/PROGRAMNAME`

**4. DB2 connection errors**
- Verify DB2 subsystem name in configuration
- Check DB2 is running and accessible
- Verify RACF permissions for DB2

### Debug Mode

Enable verbose output for detailed information:

```bash
# Verbose make
make install VERBOSE=1

# Verbose individual script
python3 03_compile_programs.py -v
```

### Check Status

```bash
# Show build system status
make status

# Show configuration
make show-config
```

## Comparison with Previous Build Systems

| Aspect | JCL-Based | Python-Based | Makefile-Based (Current) |
|--------|-----------|--------------|--------------------------|
| **Compilation** | JCL jobs | Python script | Native Makefile |
| **Incremental** | No | No | Yes |
| **Parallelization** | Limited | Thread-based | Native (`make -j`) |
| **Dependencies** | Manual | None | Automatic |
| **File Location** | MVS datasets | MVS datasets | USS files |
| **Speed** | Slow | Medium | Fast (incremental) |
| **Debugging** | Difficult | Easier | Easiest |
| **Portability** | MVS-specific | USS-specific | Standard Make |

### Why Makefile-Based Compilation?

1. **True Incremental Builds**: Only recompile changed files
2. **Automatic Dependencies**: Tracks copybook and DSECT dependencies
3. **Native Parallelization**: Use `make -j<N>` for parallel builds
4. **USS-Native**: No dataset copying overhead
5. **Standard Tools**: Uses standard GNU Make features
6. **Faster Development**: Typical recompile is seconds vs minutes

## Additional Resources

- Original JCL-based instructions: [`../doc/README.md`](../doc/README.md:1)
- CBSA GitHub repository: https://github.com/cicsdev/cics-banking-sample-application-cbsa
- CICS documentation: https://www.ibm.com/docs/en/cics-ts/

## Support

For issues or questions:
1. Check the troubleshooting section above
2. Review the original JCL-based documentation
3. Consult CICS and DB2 documentation
4. Contact your system administrator

## License

Copyright IBM Corp. 2023, 2025

This build system follows the same license as the CBSA project.