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

# Configuration (defined before includes so sub-makefiles can use these variables)
BUILD_CONFIG ?= $(mkfile_dir)/build.conf
PYTHON ?= python3
VERBOSE ?=

# Include COBOL compilation, BMS assembly, linking, and DB2 makefiles
include $(mkfile_dir)/compile.mk
include $(mkfile_dir)/assemble.mk
include $(mkfile_dir)/db2.mk

.PHONY: all help install populate verify free-plan db2bind-free-plan \
        clean-db2 clean-vsam clean-cobol-build clean-assemble-build clean-link-build clean-all \
        db2bind-clean

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
	@echo "  cobol-programs   - Compile COBOL programs"
	@echo "  assemble-maps    - Assemble BMS maps"
	@echo "  populate         - Create VSAM files and populate data"
	@echo "  verify           - Verify installation"
	@echo "  clean-cobol      - Clean COBOL build artifacts"
	@echo "  clean-assemble   - Clean BMS assembly artifacts"
	@echo "  clean-db2        - Drop DB2 artifacts"
	@echo "  clean-vsam       - Delete VSAM files"
	@echo "  clean-all        - Clean everything (DB2, VSAM, build artifacts)"
	@echo ""
	@echo "DB2 Management (from db2.mk):"
	@echo "  db2-help         - Show detailed DB2 management help"
	@echo "  db2-create       - Create all DB2 artifacts"
	@echo "  db2-bind-packages - Bind DB2 packages and plan"
	@echo "  db2-bind-all     - Bind packages and grant permissions"
	@echo "  db2-drop         - Drop all DB2 artifacts"
	@echo "  db2-rebuild      - Drop and recreate all DB2 artifacts"
	@echo ""
	@echo "COBOL Compilation (from compile.mk):"
	@echo "  help-cobol       - Show COBOL compilation help"
	@echo "  list-programs    - List all COBOL programs"
	@echo "  status-cobol     - Show COBOL build status"
	@echo ""
	@echo "BMS Assembly (from assemble.mk):"
	@echo "  help-assemble    - Show BMS assembly help"
	@echo "  list-maps        - List all BMS maps"
	@echo "  status-assemble  - Show BMS assembly status"
	@echo ""
	@echo "Options:"
	@echo "  VERBOSE=1        - Enable verbose output"
	@echo ""
	@echo "Examples:"
	@echo "  gmake install                    # Full installation"
	@echo "  gmake install VERBOSE=1          # Full installation with verbose output"
	@echo "  gmake cobol-programs             # Compile all programs"
	@echo "  gmake assemble-maps              # Assemble BMS maps"
	@echo "  gmake db2-create                 # Create DB2 database"
	@echo "  gmake db2-bind-packages          # Bind DB2 packages and plan"
	@echo "  gmake clean-all db2-create       # Clean and recreate everything"
	@echo ""

# Complete installation
install: db2-create assemble-maps cobol-programs db2-bind-packages populate verify
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
clean-db2: db2-drop
	@echo "Dropping DB2 artifacts..."

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