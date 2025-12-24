# Plan: Update batchtsocmd Version Requirement to 0.1.11

## Objective

Update all references to batchtsocmd version requirement from `>=0.1.10` to `>=0.1.11` across the codebase.

## Files to Update

### 1. setenv (Root directory)
**Location**: Lines 54-88
**Changes needed**:
- Line 54: Update comment from `>=0.1.10` to `>=0.1.11`
- Line 59: Update install message from `0.1.10` to `0.1.11`
- Line 60: Update pip install command from `batchtsocmd>=0.1.10` to `batchtsocmd>=0.1.11`
- Line 71: Update comment from `0.1.10` to `0.1.11`
- Line 72: Update version check from `0.1.10` to `0.1.11`
- Line 74: Update warning message from `0.1.10` to `0.1.11`
- Line 75: Update upgrade message from `0.1.10` to `0.1.11`
- Line 76: Update pip install command from `batchtsocmd>=0.1.10` to `batchtsocmd>=0.1.11`

### 2. etc/install/base/uss_build/requirements.txt
**Location**: Line 7-8
**Changes needed**:
- Line 7: Update comment from `0.1.10+` to `0.1.11+`
- Line 8: Update requirement from `batchtsocmd>=0.1.10` to `batchtsocmd>=0.1.11`

### 3. etc/install/base/uss_build/db2.mk
**Location**: Line 34
**Changes needed**:
- Line 34: Update comment from `batchtsocmd>=0.1.10` to `batchtsocmd>=0.1.11`

### 4. etc/install/base/uss_build/db2grant/README.md
**Location**: Line 32
**Changes needed**:
- Line 32: Update version reference from `0.1.10+` to `0.1.11+`

### 5. etc/install/base/uss_build/README.md
**Location**: No specific version mentioned in the section reviewed
**Action**: Verify if any version-specific documentation exists elsewhere in the file

## Implementation Strategy

1. **Phase 1**: Update core configuration files
   - requirements.txt (most critical - defines dependency)
   - setenv (environment setup and validation)

2. **Phase 2**: Update documentation
   - db2.mk comments
   - db2grant/README.md
   - uss_build/README.md

3. **Phase 3**: Verification
   - Search for any remaining references to 0.1.9
   - Ensure consistency across all files

## Rationale

Updating to version 0.1.11 ensures:
- Users get the latest bug fixes and improvements
- Consistent version requirements across all documentation and scripts
- Proper dependency management for the project

## Testing Considerations

After updates:
- Verify setenv script correctly detects and installs/upgrades to 0.1.11
- Confirm pip install with requirements.txt uses correct version
- Check that all documentation accurately reflects the new requirement