# CBSA USS Build System Makefile
# GNU Make-based build orchestration for CICS Banking Sample Application
SHELL := /bin/env bash
.SHELLFLAGS := -e -u -c

mkfile_path := $(abspath $(lastword $(MAKEFILE_LIST)))
mkfile_dir := $(dir $(mkfile_path))

# Common build configuration
# These variables are shared across compile.mk, assemble.mk, and link.mk

# Source directories
REL_ROOT_DIR := .
SRC_DIR := $(REL_ROOT_DIR)/src/base/cobol_src
COPY_DIR := $(REL_ROOT_DIR)/src/base/cobol_copy
BMS_SRC_DIR := $(REL_ROOT_DIR)/src/base/bms_src

# Build directories

BUILD_DIR := etc/build

OBJ_DIR := $(BUILD_DIR)/obj
DBRM_DIR := $(BUILD_DIR)/dbrm
LOAD_DIR := $(BUILD_DIR)/load
BMS_MACRO_DIR := $(BUILD_DIR)/bmsmac

# Ensure build directories exist
$(shell mkdir -p $(BMS_MACRO_DIR) $(BUILD_DIR) $(OBJ_DIR) $(DBRM_DIR) $(LOAD_DIR))

# Target MVS datasets
LOADLIB_HLQ ?= CBSA.CICSBSA
LOADLIB := $(LOADLIB_HLQ).LOADLIB
DSECT_LIB := $(LOADLIB_HLQ).DSECT

# Include COBOL compilation, BMS assembly, linking, and DB2 makefiles
include $(mkfile_dir)/compile.mk
include $(mkfile_dir)/assemble.mk
include $(mkfile_dir)/db2.mk

.PHONY: all db2bind-clean db2bind-help install setup-db2 compile assemble link db2bind populate verify \
        setup-db2-only compile-only assemble-only link-only db2bind-only populate-only \
        clean-db2 clean-vsam clean-all compile-programs compile-maps assemble-maps link-programs \
        db2bind-packages db2bind-plan db2bind-rebind-plan free-plan db2-help

# Configuration
CONFIG_FILE ?= build.conf
PYTHON ?= python3
VERBOSE ?=

# Add -v flag if VERBOSE is set
ifeq ($(VERBOSE),1)
    VERBOSE_FLAG = -v
else
    VERBOSE_FLAG =
endif

# Default target
all: help

# Help target
help:
	@echo "CBSA USS Build System"
	@echo "====================="
	@echo ""
	@echo "Available targets:"
	@echo "  install          - Complete installation (all steps)"
	@echo "  setup-db2        - Create DB2 database, tables, and indexes"
	@echo "  compile          - Compile COBOL programs"
	@echo "  compile-programs - Compile COBOL programs only"
	@echo "  assemble         - Assemble BMS maps"
	@echo "  assemble-maps    - Assemble BMS maps only"
	@echo "  link             - Link object files into load modules"
	@echo "  link-programs    - Link all programs"
	@echo "  db2bind          - Bind programs to DB2 (packages and plan)"
	@echo "  db2bind-packages - Bind DB2 packages only"
	@echo "  db2bind-plan     - Bind DB2 plan only"
	@echo "  db2bind-rebind-plan - Rebind existing DB2 plan"
	@echo "  populate         - Create VSAM files and populate data"
	@echo "  verify           - Verify installation"
	@echo "  clean            - Clean build artifacts"
	@echo "  clean-db2        - Drop DB2 artifacts"
	@echo "  clean-vsam       - Delete VSAM files"
	@echo "  clean-all        - Clean everything (DB2, VSAM, libraries)"
	@echo ""
	@echo "DB2 Management (using db2.mk):"
	@echo "  db2-help         - Show detailed DB2 management help"
	@echo "  db2-create       - Create all DB2 artifacts using JCL"
	@echo "  db2-bind-all     - Bind packages and plan using JCL"
	@echo "  db2-drop         - Drop all DB2 artifacts using JCL"
	@echo ""
	@echo "Options:"
	@echo "  VERBOSE=1      - Enable verbose output"
	@echo "  CONFIG_FILE=<file> - Use alternate configuration file"
	@echo ""
	@echo "Examples:"
	@echo "  make install                    # Full installation"
	@echo "  make install VERBOSE=1          # Full installation with verbose output"
	@echo "  make compile                    # Compile all programs"
	@echo "  make compile-programs           # Compile programs only"
	@echo "  make assemble                   # Assemble all BMS maps"
	@echo "  make assemble-maps              # Assemble BMS maps only"
	@echo "  make link                       # Link all programs"
	@echo "  make link-programs              # Link all programs"
	@echo "  make db2bind                    # Bind all packages and plan"
	@echo "  make db2bind-rebind-plan        # Quick plan rebind"
	@echo "  make clean-db2 setup-db2        # Recreate DB2 artifacts"
	@echo ""
	@echo "For detailed help:"
	@echo "  make db2bind-help               # Show DB2 binding-specific help"
	@echo "  make db2-help                   # Show DB2 management help (JCL-based)"
	@echo ""

# Complete installation
install: db2-create assemble-maps cobol-programs link-programs db2-bind-packages db2-bind-plan populate verify
	@echo ""
	@echo "=========================================="
	@echo "CBSA Installation Complete!"
	@echo "=========================================="
	@echo ""
	@echo "Next steps:"
	@echo "1. Update CICS region configuration (see documentation)"
	@echo "2. Copy z/OS Connect artifacts to server"
	@echo "3. Restart CICS region and z/OS Connect server"
	@echo ""


# Free plan and packages (now using db2.mk targets)
free-plan:
	@echo ""
	@echo "=========================================="
	@echo "Freeing DB2 Plan and Packages"
	@echo "=========================================="
	@$(MAKE) db2-drop
	@echo "Note: Use db2-drop to remove all DB2 artifacts"

# Alias for free-plan
db2bind-free-plan: free-plan

# Step 5: Populate data
populate:
	@echo ""
	@echo "=========================================="
	@echo "Step 5: Populating Data"
	@echo "=========================================="
	$(PYTHON) 05_populate_data.py -c $(CONFIG_FILE) $(VERBOSE_FLAG)

# Verify installation
verify:
	@echo ""
	@echo "=========================================="
	@echo "Verifying Installation"
	@echo "=========================================="
	$(PYTHON) 05_populate_data.py -c $(CONFIG_FILE) --verify-only $(VERBOSE_FLAG)

# Clean targets (now using db2.mk targets)
clean-db2:
	@echo "Dropping DB2 artifacts..."
	@$(MAKE) db2-drop

clean-vsam:
	@echo "Deleting VSAM files..."
	@echo "Note: Manual deletion may be required via IDCAMS"

clean-cobol-build: clean-cobol

clean-assemble-build: clean-assemble

clean-link-build: clean-link

clean-all: clean-db2 clean-vsam clean-cobol clean-assemble clean-link
	@echo "Complete cleanup performed"
	@echo "Note: MVS libraries are not automatically deleted"
	@echo "      Use TSO DELETE command if needed"

db2bind-clean: clean-db2
	@echo "DB2 bind artifacts cleaned"