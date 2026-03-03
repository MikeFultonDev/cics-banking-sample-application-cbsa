# Unreferenced Python Scripts Analysis

This document identifies Python scripts in the `etc/install/base/uss_build` directory that are NOT currently referenced by the active build system (Makefiles).

## Analysis Date
2026-03-03

## Currently Used Scripts

### Active in Makefiles
1. **05_populate_data.py** - ✅ USED
   - Referenced in: `Makefile` (populate and verify targets)
   - Purpose: Create VSAM files and populate data

2. **bin/db2subst** - ✅ USED
   - Referenced in: `db2.mk` (DB2SUBST variable)
   - Purpose: Substitute ${VAR} references in DB2 SQL files using build.conf values

3. **cbsa_utils.py** - ⚠️ POTENTIALLY USED
   - May be imported by other Python scripts
   - Purpose: Common utility functions

## Unreferenced Scripts

### Development/Testing Scripts
These scripts appear to be for development, testing, or examples and are not part of the active build process:

1. **bin/ebcdic_converter_fcntl.py**
   - Purpose: EBCDIC conversion using z/OS fcntl file tagging
   - Status: Standalone utility, not referenced in build system
   - Note: Part of zos_ebcdic_converter package development

2. **bin/test_ebcdic_converter.py**
   - Purpose: Test driver for ebcdic_converter_fcntl
   - Status: Test script, not part of build process
   - Note: Duplicate exists in zos_ebcdic_converter/tests/

3. **bin/example_service_usage.py**
   - Purpose: Usage examples for EBCDIC converter
   - Status: Example/documentation script
   - Note: Duplicate exists in zos_ebcdic_converter/examples/

4. **bin/find_fcntl_constants.py**
   - Purpose: Find fcntl constants on z/OS system
   - Status: Development/diagnostic utility
   - Note: Used during package development, not in production build

5. **bin/test_constant_18.py**
   - Purpose: Test specific fcntl constant
   - Status: Development/testing utility
   - Note: Not referenced in build system

### Package Development Files
The `zos_ebcdic_converter/` directory contains a complete Python package with its own structure:

6. **zos_ebcdic_converter/setup.py**
   - Purpose: Package installation configuration
   - Status: Package development file, not used in CBSA build

7. **zos_ebcdic_converter/zos_ebcdic_converter/__init__.py**
   - Purpose: Package initialization
   - Status: Part of package structure

8. **zos_ebcdic_converter/zos_ebcdic_converter/converter.py**
   - Purpose: Core EBCDIC conversion logic
   - Status: Package module

9. **zos_ebcdic_converter/zos_ebcdic_converter/cli.py**
   - Purpose: Command-line interface for package
   - Status: Package module

10. **zos_ebcdic_converter/tests/test_ebcdic_converter.py**
    - Purpose: Package test suite
    - Status: Test file

11. **zos_ebcdic_converter/examples/example_service_usage.py**
    - Purpose: Package usage examples
    - Status: Example file

## Deprecated Scripts (Mentioned in README)

According to `README.md`, these scripts were replaced by Makefiles:

1. **01_create_libraries.py** - NOT FOUND (already removed)
   - Replaced by: Makefile targets
   - Status: Deprecated and removed

2. **02_setup_db2.py** - NOT FOUND (already removed)
   - Replaced by: `db2.mk` targets
   - Status: Deprecated and removed

3. **03_compile_programs.py** - NOT FOUND (already removed)
   - Replaced by: `compile.mk` targets
   - Status: Deprecated and removed

4. **04_bind_db2.py** - NOT FOUND (already removed)
   - Replaced by: `db2.mk` db2-bind-packages target
   - Status: Deprecated and removed

## Recommendations

### Keep (Active Build System)
- `05_populate_data.py` - Currently used
- `bin/db2subst` - Currently used
- `cbsa_utils.py` - May be imported by active scripts

### Consider Removing (Not Part of Build)
The following scripts are not referenced in the build system but may have value for development/testing:

- `bin/ebcdic_converter_fcntl.py` - Standalone utility
- `bin/test_ebcdic_converter.py` - Test script
- `bin/example_service_usage.py` - Example script
- `bin/find_fcntl_constants.py` - Development utility
- `bin/test_constant_18.py` - Test utility

### Package Directory
The `zos_ebcdic_converter/` directory appears to be a complete Python package for EBCDIC conversion. Consider:
- Moving to a separate repository if it's a reusable component
- Keeping if it's actively maintained as part of CBSA
- Documenting its relationship to the CBSA build system

## Notes

1. The build system has been successfully migrated from Python scripts to Makefiles
2. Only `05_populate_data.py` and `bin/db2subst` remain as active Python components
3. The EBCDIC converter package appears to be a separate utility that could be extracted
4. Test and example scripts are useful for development but not required for production builds