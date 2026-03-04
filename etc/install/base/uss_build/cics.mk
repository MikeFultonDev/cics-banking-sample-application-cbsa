# CBSA CICS Configuration Management Makefile
# Manages CICS dataset allocation and resource definitions using CSD (CICS System Definition)
# Copyright IBM Corp. 2023, 2025

.PHONY: cics-help cics-create

# CICS CSD directory
CICSCSD_DIR := $(mkfile_dir)/cicscsd

# build.conf path and envsubst utility for variable substitution
# Use = (deferred) so $(PYTHON) expands at use time (PYTHON is defined in parent Makefile)
BUILD_CONF = $(mkfile_dir)/build.conf
ENVSUBST   = $(PYTHON) $(mkfile_dir)/bin/envsubst

# Verbose flag
VERBOSE_FLAG := $(if $(VERBOSE),-v,)

# CICS Help
cics-help:
	@echo "CBSA CICS Configuration Management Targets"
	@echo "==========================================="
	@echo ""
	@echo "CICS Resource Definition:"
	@echo "  cics-create            - Create CICS datasets and install resource definitions (CSD)"
	@echo ""
	@echo "Configuration file: $(BUILD_CONF)"
	@echo ""

# Create CICS datasets and install resource definitions
# Uses cics_create.py to:
# - Pre-allocate required CICS datasets (DFHCSD) with proper VSAM attributes
# - Substitute variables in cicscsd/BANK.csd
# - Execute DFHCSDUP to install CSD definitions
cics-create:
	@echo "Creating CICS datasets and installing resource definitions..."
	$(PYTHON) $(mkfile_dir)/cics_create.py \
	    --config $(BUILD_CONF) \
	    --csd-file $(CICSCSD_DIR)/BANK.csd \
	    $(VERBOSE_FLAG)
	@echo ""

# Made with Bob