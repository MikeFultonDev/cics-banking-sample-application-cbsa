# Link-Edit (Bind) Process for CICS Banking Sample Application

This document describes how object files are bound together to create executable load modules for the CBSA application.

## Overview

The link-edit process (also called binding) takes compiled object files and combines them with necessary system libraries to create executable load modules. Each `.lked` file in this directory contains link-edit control statements for a specific program.

## Link-Edit Control Statement Format

All link-edit control files follow a standard format:

```
    INCLUDE CBSAMOD(programname)
    [INCLUDE SYSLIB(library)]
    ENTRY programname
    NAME programname(R)
```

### Control Statement Descriptions

1. **INCLUDE CBSAMOD(programname)**
   - Includes the compiled object module from the CBSAMOD dataset
   - CBSAMOD is the partitioned dataset containing compiled COBOL object files
   - The object file name matches the program name

2. **INCLUDE SYSLIB(library)** (optional)
   - Includes additional system libraries required by the program
   - Used for programs that need DB2 or CICS runtime support
   - Common libraries:
     - `DSNELI` - DB2 Language Interface module
     - `DFHNCTR` - CICS runtime support

3. **ENTRY programname**
   - Specifies the entry point (starting address) of the load module
   - The entry point name matches the program name

4. **NAME programname(R)**
   - Assigns a name to the output load module
   - The `(R)` indicates the module is reentrant (can be shared by multiple tasks)

## Program Categories

### Standard CICS Programs (Most Programs)

Most programs use a simple link-edit with only the object module:

```
    INCLUDE CBSAMOD(programname)
    ENTRY programname
    NAME programname(R)
```

**Programs in this category:**
- ABNDPROC
- BNK1CAC
- BNK1CCA
- BNK1CCS
- BNK1CRA
- BNK1DAC
- BNK1DCS
- BNK1TFN
- BNK1UAC
- BNKMENU
- CRDTAGY1
- CRDTAGY2
- CRDTAGY3
- CRDTAGY4
- CRDTAGY5
- CREACC
- CRECUST
- DBCRFUN
- DELACC
- DELCUS
- EXTDCUST
- GETCOMPY
- GETSCODE
- INQACC
- INQACCCU
- INQCUST
- UPDACC
- UPDCUST
- XFRFUN

### Batch Programs with DB2 Support

The BANKDATA program requires additional DB2 and CICS libraries:

```
    INCLUDE CBSAMOD(BANKDATA)
    INCLUDE SYSLIB(DSNELI)
    INCLUDE SYSLIB(DFHNCTR)
    ENTRY BANKDATA
    NAME BANKDATA(R)
```

**Additional libraries:**
- `DSNELI` - DB2 Language Interface (required for DB2 SQL operations)
- `DFHNCTR` - CICS runtime support

## Link-Edit Process Flow

1. **Input**: Compiled object file from CBSAMOD dataset
2. **Processing**: 
   - Link-editor (IEWL or IEWBLINK) reads the `.lked` control statements
   - Resolves external references
   - Includes required system libraries
   - Sets entry point and module attributes
3. **Output**: Executable load module in LOADLIB dataset

## USS Build System Integration

For USS-based builds using the `ld` command, the equivalent operations would be:

### Standard Programs
```bash
ld -o programname \
   -e programname \
   programname.o
```

### Programs with DB2 Support
```bash
ld -o BANKDATA \
   -e BANKDATA \
   BANKDATA.o \
   -l dsneli \
   -l dfhnctr
```

## Key Characteristics

1. **Reentrant Modules**: All programs are marked as reentrant `(R)`, allowing them to be shared by multiple concurrent tasks
2. **Single Object Input**: Each program is built from a single compiled object file
3. **Minimal Dependencies**: Most programs have no external library dependencies beyond CICS runtime
4. **Consistent Naming**: Entry point, module name, and object file name all match the program name

## Notes

- The link-edit control files are used as input to the MVS link-editor (binder)
- These files do not need to be edited unless changing program dependencies
- All programs follow the same basic pattern with only BANKDATA requiring additional libraries
- The `(R)` attribute is critical for CICS programs to support multi-threading

## Summary

| Category | Count | Additional Libraries |
|----------|-------|---------------------|
| Standard CICS Programs | 29 | None |
| Batch Programs with DB2 | 1 (BANKDATA) | DSNELI, DFHNCTR |
| **Total** | **30** | |
