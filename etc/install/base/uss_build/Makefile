# CBSA USS Build System Makefile
# GNU Make-based build orchestration for CICS Banking Sample Application

# Common build configuration
# These variables are shared across compile.mk, assemble.mk, and link.mk

# Source directories
SRC_DIR := ../../../src/base/cobol_src
COPY_DIR := ../../../src/base/cobol_copy
BMS_SRC_DIR := ../../../src/base/bms_src

# Build directories
BUILD_DIR := build
OBJ_DIR := $(BUILD_DIR)/obj
DBRM_DIR := $(BUILD_DIR)/dbrm
DSECT_DIR := $(BUILD_DIR)/dsect

# Target MVS datasets
LOADLIB_HLQ ?= CBSA.CICSBSA
LOADLIB := $(LOADLIB_HLQ).LOADLIB
DSECT_LIB := $(LOADLIB_HLQ).DSECT

# Include COBOL compilation, BMS assembly, linking, and DB2 makefiles
include compile.mk
include assemble.mk
include link.mk
include db2.mk

.PHONY: all db2bind-clean db2bind-help install setup-db2 compile assemble link db2bind populate verify \
        create-libs setup-db2-only compile-only assemble-only link-only db2bind-only populate-only \
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
	@echo "  create-libs      - Create MVS libraries and copy source files"
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
install: create-libs setup-db2 compile assemble link db2bind populate verify
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

# Step 1: Create libraries
create-libs:
	@echo ""
	@echo "=========================================="
	@echo "Step 1: Creating Libraries"
	@echo "=========================================="
	$(PYTHON) 01_create_libraries.py -c $(CONFIG_FILE) $(VERBOSE_FLAG)

# Step 2: Setup DB2 (now using db2.mk targets)
setup-db2:
	@echo ""
	@echo "=========================================="
	@echo "Step 2: Setting up DB2"
	@echo "=========================================="
	@$(MAKE) db2-create

# Step 3: Compile programs
compile: compile-programs
	@echo ""
	@echo "=========================================="
	@echo "Compilation Complete"
	@echo "=========================================="

# Step 3.5: Assemble BMS maps
assemble: assemble-maps
	@echo ""
	@echo "=========================================="
	@echo "BMS Assembly Complete"
	@echo "=========================================="

# Step 4: Link programs
link: link-programs
	@echo ""
	@echo "=========================================="
	@echo "Link-Edit Complete"
	@echo "=========================================="

# Compile COBOL programs only (using compile.mk)
compile-programs:
	@echo ""
	@echo "=========================================="
	@echo "Step 3a: Compiling COBOL Programs"
	@echo "=========================================="
	@$(MAKE) cobol-programs

# Alias for backward compatibility
compile-maps: assemble-maps

# Step 5: Bind to DB2
db2bind: db2bind-packages db2bind-plan
	@echo ""
	@echo "=========================================="
	@echo "DB2 Binding Complete"
	@echo "=========================================="

# Bind packages only (now using db2.mk targets)
db2bind-packages:
	@echo ""
	@echo "=========================================="
	@echo "Step 4a: Binding DB2 Packages"
	@echo "=========================================="
	@$(MAKE) db2-bind-packages

# Bind plan only (requires packages) (now using db2.mk targets)
db2bind-plan:
	@echo ""
	@echo "=========================================="
	@echo "Step 4b: Binding DB2 Plan"
	@echo "=========================================="
	@$(MAKE) db2-bind-plan

# Rebind plan (faster than full db2bind) (now using db2.mk targets)
db2bind-rebind-plan:
	@echo ""
	@echo "=========================================="
	@echo "Rebinding DB2 Plan"
	@echo "=========================================="
	@$(MAKE) db2-bind-plan

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

# Individual component builds
setup-db2-only: setup-db2

compile-only: compile

assemble-only: assemble

link-only: link

db2bind-only: db2bind

populate-only: populate


# Rebuild targets
rebuild-db2: clean-db2 setup-db2 db2bind populate

rebuild-compile: compile assemble link db2bind

# DB2 Bind help
db2bind-help:
	@echo "DB2 Binding Help"
	@echo "================"
	@echo ""
	@echo "Available DB2 binding targets:"
	@echo "  db2bind               - Bind all packages and plan"
	@echo "  db2bind-packages      - Bind DB2 packages only"
	@echo "  db2bind-plan          - Bind DB2 plan only"
	@echo "  db2bind-rebind-plan   - Rebind existing plan (faster)"
	@echo "  free-plan             - Free DB2 plan and packages"
	@echo "  db2bind-free-plan     - Alias for free-plan"
	@echo ""
	@echo "Options:"
	@echo "  VERBOSE=1        - Enable verbose output"
	@echo "  CONFIG_FILE=file - Use alternate configuration"
	@echo ""
	@echo "Examples:"
	@echo "  make db2bind                 # Full DB2 bind"
	@echo "  make db2bind-packages        # Packages only"
	@echo "  make db2bind-rebind-plan     # Quick rebind"
	@echo "  make free-plan               # Clean up bindings"
	@echo ""
	@echo ""

rebuild-db2bind: clean-db2 db2bind

rebuild-all: clean-all install

# Parallel compilation (GNU Make handles this natively)
compile-parallel:
	@echo "Compiling with parallel execution..."
	@echo "Use: make -j4 compile"
	@echo "This will compile up to 4 programs simultaneously"

# Quick build (skip data population)
quick-install: create-libs setup-db2 compile bind
	@echo ""
	@echo "Quick installation complete (data population skipped)"
	@echo "Run 'make populate' to populate data"

# Development targets
dev-compile: compile-programs

dev-maps: compile-maps

# Single program compilation (using compile.mk)
compile-program:
	@if [ -z "$(PROGRAM)" ]; then \
		echo "Error: PROGRAM variable not set"; \
		echo "Usage: make compile-program PROGRAM=<program-name>"; \
		exit 1; \
	fi
	@echo "Compiling program: $(PROGRAM)"
	@$(MAKE) $(LOAD_DIR)/$(PROGRAM)

# Status check
bind-status:
	@echo "CBSA Build System Status"
	@echo "========================"
	@echo ""
	@echo "Configuration file: $(CONFIG_FILE)"
	@if [ -f $(CONFIG_FILE) ]; then \
		echo "✓ Configuration file exists"; \
	else \
		echo "✗ Configuration file not found"; \
	fi
	@echo ""
	@echo "Python scripts:"
	@for script in 01_create_libraries.py 02_setup_db2.py 03_compile_programs.py \
	               04_bind_db2.py 05_populate_data.py cbsa_utils.py; do \
		if [ -f $$script ]; then \
			echo "  ✓ $$script"; \
		else \
			echo "  ✗ $$script (missing)"; \
		fi \
	done
	@echo ""

# Make scripts executable
setup-scripts:
	@echo "Making Python scripts executable..."
	@chmod +x *.py
	@echo "✓ Scripts are now executable"

# Show configuration
show-config:
	@echo "Current Configuration:"
	@echo "====================="
	@cat $(CONFIG_FILE) | grep -v "^#" | grep -v "^$$"