# CBSA USS Build System Makefile
# GNU Make-based build orchestration for CICS Banking Sample Application

.PHONY: all clean help install setup-db2 compile bind populate verify \
        create-libs setup-db2-only compile-only bind-only populate-only \
        clean-db2 clean-vsam clean-all compile-programs compile-maps \
        bind-packages bind-plan rebind-plan free-plan

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

# Include the compilation and binding Makefiles
include compile.mk
include bind.mk

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
	@echo "  compile          - Compile COBOL programs and assemble BMS maps"
	@echo "  compile-programs - Compile COBOL programs only"
	@echo "  compile-maps     - Assemble BMS maps only"
	@echo "  bind             - Bind programs to DB2 (packages and plan)"
	@echo "  bind-packages    - Bind DB2 packages only"
	@echo "  bind-plan        - Bind DB2 plan only"
	@echo "  rebind-plan      - Rebind existing DB2 plan"
	@echo "  populate         - Create VSAM files and populate data"
	@echo "  verify           - Verify installation"
	@echo "  clean            - Clean build artifacts"
	@echo "  clean-db2        - Drop DB2 artifacts"
	@echo "  clean-vsam       - Delete VSAM files"
	@echo "  clean-all        - Clean everything (DB2, VSAM, libraries)"
	@echo ""
	@echo "Options:"
	@echo "  VERBOSE=1      - Enable verbose output"
	@echo "  CONFIG_FILE=<file> - Use alternate configuration file"
	@echo ""
	@echo "Examples:"
	@echo "  make install                    # Full installation"
	@echo "  make install VERBOSE=1          # Full installation with verbose output"
	@echo "  make compile                    # Compile all programs and maps"
	@echo "  make compile-programs           # Compile programs only"
	@echo "  make build/load/CREACC          # Compile single program (incremental)"
	@echo "  make bind                       # Bind all packages and plan"
	@echo "  make build/bind/CREACC.pkg      # Bind single package (incremental)"
	@echo "  make rebind-plan                # Quick plan rebind"
	@echo "  make clean-db2 setup-db2        # Recreate DB2 artifacts"
	@echo ""
	@echo "For detailed help:"
	@echo "  make -f compile.mk help         # Show compilation-specific help"
	@echo "  make -f bind.mk help-bind       # Show binding-specific help"
	@echo ""

# Complete installation
install: create-libs setup-db2 compile bind populate verify
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

# Step 2: Setup DB2
setup-db2:
	@echo ""
	@echo "=========================================="
	@echo "Step 2: Setting up DB2"
	@echo "=========================================="
	$(PYTHON) 02_setup_db2.py -c $(CONFIG_FILE) $(VERBOSE_FLAG)

# Step 3: Compile programs (now uses compile.mk)
compile: programs maps
	@echo ""
	@echo "=========================================="
	@echo "Step 3: Compilation Complete"
	@echo "=========================================="
	@echo "✓ All COBOL programs compiled"
	@echo "✓ All BMS maps assembled"
	@echo ""

# Compile programs only
compile-programs: programs

# Compile maps only
compile-maps: maps

# Step 4: Bind to DB2 (now uses bind.mk)
bind: bind-all
	@echo ""
	@echo "=========================================="
	@echo "Step 4: DB2 Binding Complete"
	@echo "=========================================="
	@echo "✓ All DB2 packages bound"
	@echo "✓ DB2 plan bound"
	@echo ""

# Bind packages only
bind-packages: packages

# Bind plan only (requires packages)
bind-plan: plan

# Rebind plan (faster than full bind)
rebind-plan:
	@echo ""
	@echo "=========================================="
	@echo "Rebinding DB2 Plan"
	@echo "=========================================="
	@$(MAKE) -f bind.mk rebind-plan

# Free plan and packages
free-plan:
	@echo ""
	@echo "=========================================="
	@echo "Freeing DB2 Plan and Packages"
	@echo "=========================================="
	@$(MAKE) -f bind.mk free-plan

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

# Clean targets
clean-db2:
	@echo "Dropping DB2 artifacts..."
	$(PYTHON) 02_setup_db2.py -c $(CONFIG_FILE) --drop-only $(VERBOSE_FLAG)

clean-vsam:
	@echo "Deleting VSAM files..."
	@echo "Note: Manual deletion may be required via IDCAMS"

clean-all: clean-db2 clean-vsam
	@echo "Complete cleanup performed"
	@echo "Note: MVS libraries are not automatically deleted"
	@echo "      Use TSO DELETE command if needed"

clean: clean-db2
	@echo "Build artifacts cleaned"

# Individual component builds
setup-db2-only: setup-db2

compile-only: compile

bind-only: bind

populate-only: populate

# Bind-specific aliases
bind-db2: bind
bind-db2-only: bind

# Rebuild targets
rebuild-db2: clean-db2 setup-db2 bind populate

rebuild-compile: compile bind

rebuild-bind: clean-bind bind

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

# Development targets (now use compile.mk)
dev-compile: compile-programs

dev-maps: compile-maps

# Single program compilation (use compile.mk targets directly)
compile-program:
	@if [ -z "$(PROGRAM)" ]; then \
		echo "Error: PROGRAM variable not set"; \
		echo "Usage: make compile-program PROGRAM=<program-name>"; \
		echo "Or directly: make build/load/<PROGRAM>"; \
		exit 1; \
	fi
	@echo "Compiling program: $(PROGRAM)"
	@$(MAKE) -f compile.mk build/load/$(PROGRAM)

# Status check
status:
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
	@echo "Build system:"
	@if [ -f compile.mk ]; then \
		echo "  ✓ compile.mk (Makefile-based compilation)"; \
	else \
		echo "  ✗ compile.mk (missing)"; \
	fi
	@if [ -f bind.mk ]; then \
		echo "  ✓ bind.mk (Makefile-based DB2 binding)"; \
	else \
		echo "  ✗ bind.mk (missing)"; \
	fi
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