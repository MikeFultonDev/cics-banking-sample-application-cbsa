# EBCDIC Converter Migration to PyPI Package

## Overview

The CBSA project has migrated from using a local EBCDIC converter implementation to the published `zos-ccsid-converter` package available on PyPI at https://pypi.org/project/zos-ccsid-converter.

## What Changed

### 1. Package Source

**Before:**
- Local implementation in `etc/install/base/uss_build/bin/ebcdic_converter_fcntl.py`
- Local package in `etc/install/base/uss_build/zos_ebcdic_converter/`

**After:**
- Published package: `zos-ccsid-converter` from PyPI
- Version: 0.1.5 or later

### 2. Code Changes

#### batchtsocmd.py

**Before:**
```python
def get_file_encoding(path: str, verbose: bool = False) -> str:
    """Get the encoding tag of a file using ls -T command."""
    # ... implementation using subprocess and ls -T ...

def convert_to_ebcdic(input_path: str, output_path: str, verbose: bool = False) -> bool:
    """Convert input file from ASCII to EBCDIC if needed."""
    encoding = get_file_encoding(input_path, verbose)
    # ... manual conversion logic ...
```

**After:**
```python
from zos_ccsid_converter import CodePageService

def convert_to_ebcdic(input_path: str, output_path: str, verbose: bool = False) -> bool:
    """Convert input file from ASCII to EBCDIC using zos-ccsid-converter package."""
    service = CodePageService(verbose=verbose)
    stats = service.convert_file(input_path, output_path, target_encoding='IBM-1047')
    return stats['success']
```

### 3. Dependencies

A new `requirements.txt` file has been added:

```txt
# Python dependencies for CBSA USS build scripts
zos-ccsid-converter>=0.1.5
```

## Benefits of Migration

1. **Maintained Package**: The converter is now maintained as a separate, general-purpose utility
2. **Better Testing**: The published package has comprehensive test coverage
3. **Improved Performance**: Uses optimized fcntl system calls for file tag detection
4. **Consistent API**: Standardized interface across projects
5. **Version Control**: Proper semantic versioning and release management
6. **Community Support**: Available to the wider z/OS Python community

## Installation

### For New Installations

```bash
# Install Python dependencies
pip install -r requirements.txt
```

### For Existing Installations

```bash
# Install the new package
pip install zos-ccsid-converter>=0.1.5
```

## API Compatibility

The published package maintains API compatibility with the local implementation:

| Feature | Local Implementation | Published Package |
|---------|---------------------|-------------------|
| Code page detection | `get_file_encoding()` | `service.get_encoding_name()` |
| File conversion | `convert_to_ebcdic()` | `service.convert_file()` |
| Byte conversion | Not available | `service.convert_to_ebcdic()` |
| CCSID detection | Not available | `service.get_ccsid()` |

## Backward Compatibility

The local implementation files remain in place for reference and backward compatibility:

- `etc/install/base/uss_build/bin/ebcdic_converter_fcntl.py` - Original standalone script
- `etc/install/base/uss_build/zos_ebcdic_converter/` - Local package implementation
- `etc/install/base/uss_build/bin/test_ebcdic_converter.py` - Test suite
- `etc/install/base/uss_build/bin/example_service_usage.py` - Usage examples

These files are preserved for:
- Reference documentation
- Backward compatibility if needed
- Understanding the implementation details

## Package Information

- **Package Name**: `zos-ccsid-converter`
- **PyPI URL**: https://pypi.org/project/zos-ccsid-converter
- **GitHub**: https://github.com/MikeFultonDev/zos_ccsid_converter
- **Version**: 0.1.5+
- **Python Requirement**: Python 3.12+
- **License**: Apache 2.0

## Usage Examples

### Basic File Conversion

```python
from zos_ccsid_converter import CodePageService

service = CodePageService()

# Convert a file to EBCDIC
stats = service.convert_file('input.txt', 'output.txt')
if stats['success']:
    print(f"Converted {stats['bytes_read']} bytes")
```

### Detect File Encoding

```python
from zos_ccsid_converter import CodePageService

service = CodePageService()

# Get encoding name
encoding = service.get_encoding_name('/path/to/file')
print(f"File encoding: {encoding}")

# Get CCSID
ccsid = service.get_ccsid('/path/to/file')
print(f"File CCSID: {ccsid}")

# Check file type
if service.is_ascii('/path/to/file'):
    print("File is ASCII")
elif service.is_ebcdic('/path/to/file'):
    print("File is EBCDIC")
```

### Convert Bytes

```python
from zos_ccsid_converter import CodePageService

service = CodePageService()

# Convert ASCII bytes to EBCDIC
ascii_data = b"Hello World"
ebcdic_data = service.convert_to_ebcdic(ascii_data)

# Convert EBCDIC bytes to ASCII
ascii_back = service.convert_to_ascii(ebcdic_data)
```

## Troubleshooting

### Import Error

If you see:
```
ImportError: No module named 'zos_ccsid_converter'
```

Solution:
```bash
pip install zos-ccsid-converter
```

### Version Mismatch

If you encounter API differences, ensure you have the correct version:
```bash
pip install --upgrade zos-ccsid-converter>=0.1.5
```

### Verify Installation

```bash
# Check installed version
pip show zos-ccsid-converter

# Test the package
python3 -c "from zos_ccsid_converter import CodePageService; print('OK')"
```

## Migration Checklist

- [x] Install `zos-ccsid-converter` package
- [x] Update imports in `batchtsocmd.py`
- [x] Test file conversion functionality
- [x] Verify EBCDIC/ASCII detection works
- [x] Update documentation
- [x] Add `requirements.txt` file

## Support

For issues with the published package:
- PyPI: https://pypi.org/project/zos-ccsid-converter
- GitHub Issues: https://github.com/MikeFultonDev/zos_ccsid_converter/issues

For CBSA-specific issues:
- CBSA GitHub: https://github.com/cicsdev/cics-banking-sample-application-cbsa

## References

- [Published Package README](https://github.com/MikeFultonDev/zos_ccsid_converter/blob/main/README.md)
- [Local Implementation README](bin/README_ebcdic_converter.md)
- [CBSA Build System README](README.md)

---

**Migration Date**: December 2024  
**Package Version**: 0.1.5  
**Python Version**: 3.12+