# CBSA Link-Edit Makefile
# Incremental linking using ld command in USS
# Copyright IBM Corp. 2023, 2025

.PHONY: clean-link help-link list-link-programs status-link

# Note: Common variables (BUILD_DIR, OBJ_DIR, LOADLIB_HLQ, LOADLIB)
# are defined in the main Makefile

# Link-specific directories
LINK_DIR := $(BUILD_DIR)/link
LINK_STAMP_DIR := $(LINK_DIR)/stamps

# Link command
LD := ldc
LD_FLAGS := -b rent -b case=mixed

# Standard CICS programs (29 programs)
STANDARD_PROGRAMS := ABNDPROC BNK1CAC BNK1CCA BNK1CCS BNK1CRA BNK1DAC BNK1DCS \
                     BNK1TFN BNK1UAC BNKMENU CRDTAGY1 CRDTAGY2 CRDTAGY3 CRDTAGY4 \
                     CRDTAGY5 CREACC CRECUST DBCRFUN DELACC DELCUS EXTDCUST \
                     GETCOMPY GETSCODE INQACC INQACCCU INQCUST UPDACC UPDCUST XFRFUN

# Batch programs with DB2 support (1 program)
DB2_PROGRAMS := BANKDATA

# All programs
ALL_LINK_PROGRAMS := $(STANDARD_PROGRAMS) $(DB2_PROGRAMS)

# Stamp files (used to track when MVS load modules are up to date)
STANDARD_STAMPS := $(addprefix $(LINK_STAMP_DIR)/,$(addsuffix .stamp,$(STANDARD_PROGRAMS)))
DB2_STAMPS := $(addprefix $(LINK_STAMP_DIR)/,$(addsuffix .stamp,$(DB2_PROGRAMS)))
ALL_STAMPS := $(STANDARD_STAMPS) $(DB2_STAMPS)

# Target for linking all programs
link-programs: $(ALL_STAMPS)
	@echo "✓ Link-edit complete: $(words $(ALL_STAMPS)) programs linked"

# Create link directories
$(LINK_DIR) $(LINK_STAMP_DIR):
	@mkdir -p $@

# Link standard CICS programs
# Pattern: object file -> MVS load module (tracked by stamp file)
$(LINK_STAMP_DIR)/%.stamp: $(OBJ_DIR)/%.o | $(LINK_DIR) $(LINK_STAMP_DIR)
	@echo "Linking program: $* -> $(LOADLIB)($*)"
	@$(LD) $(LD_FLAGS) \
		-e $* \
		-o "//$(LOADLIB)($*)" \
		$<
	@touch $@
	@echo "✓ $* linked successfully"

# Link BANKDATA with DB2 support
# Note: DB2 libraries (DSNELI, DFHNCTR) are linked from system datasets
$(LINK_STAMP_DIR)/BANKDATA.stamp: $(OBJ_DIR)/BANKDATA.o | $(LINK_DIR) $(LINK_STAMP_DIR)
	@echo "Linking program: BANKDATA -> $(LOADLIB)(BANKDATA) [with DB2 support]"
	@$(LD) $(LD_FLAGS) \
		-e BANKDATA \
		-o "//$(LOADLIB)(BANKDATA)" \
		$< \
		-l //DSNC10.SDSNLOAD:DSNELI \
		-l //DFH560.CICS.SDFHLOAD:DFHNCTR
	@touch $@
	@echo "✓ BANKDATA linked successfully"

# Clean link artifacts
clean-link:
	@echo "Cleaning link artifacts..."
	@rm -rf $(LINK_DIR)
	@echo "✓ Link clean complete"

# Help target
help-link:
	@echo "CBSA Link-Edit Makefile"
	@echo "======================="
	@echo ""
	@echo "Usage:"
	@echo "  make link-programs              - Link all programs"
	@echo "  make $(LINK_STAMP_DIR)/<PROG>.stamp - Link specific program"
	@echo "  make clean-link                 - Remove link artifacts"
	@echo "  make list-link-programs         - List all programs"
	@echo "  make status-link                - Show link status"
	@echo ""
	@echo "Examples:"
	@echo "  make link-programs                      # Link all programs"
	@echo "  make $(LINK_STAMP_DIR)/CREACC.stamp     # Link CREACC only"
	@echo "  make -j4 link-programs                  # Link with 4 parallel jobs"
	@echo "  make clean-link link-programs           # Clean and relink all"
	@echo ""
	@echo "Programs:"
	@echo "  Standard CICS: $(words $(STANDARD_PROGRAMS))"
	@echo "  DB2 Programs: $(words $(DB2_PROGRAMS))"
	@echo "  Total: $(words $(ALL_LINK_PROGRAMS))"
	@echo ""
	@echo "Target MVS Dataset: $(LOADLIB)"
	@echo ""
	@echo "Note: Stamp files in $(LINK_STAMP_DIR) track link status"
	@echo ""

# List all programs
list-link-programs:
	@echo "Standard CICS Programs ($(words $(STANDARD_PROGRAMS))):"
	@for prog in $(STANDARD_PROGRAMS); do echo "  $$prog"; done
	@echo ""
	@echo "DB2 Programs ($(words $(DB2_PROGRAMS))):"
	@for prog in $(DB2_PROGRAMS); do echo "  $$prog"; done
	@echo ""
	@echo "Total: $(words $(ALL_LINK_PROGRAMS)) programs"

# Show link status
status-link:
	@echo "Link Status"
	@echo "==========="
	@echo ""
	@echo "Object directory: $(OBJ_DIR)"
	@if [ -d "$(OBJ_DIR)" ]; then \
		echo "  ✓ Object directory exists"; \
		echo "  Objects: $$(ls -1 $(OBJ_DIR)/*.o 2>/dev/null | wc -l)"; \
	else \
		echo "  ✗ Object directory not found"; \
	fi
	@echo ""
	@echo "Link stamp directory: $(LINK_STAMP_DIR)"
	@if [ -d "$(LINK_STAMP_DIR)" ]; then \
		echo "  ✓ Stamp directory exists"; \
		echo "  Stamps: $$(ls -1 $(LINK_STAMP_DIR)/*.stamp 2>/dev/null | wc -l)"; \
	else \
		echo "  ✗ Stamp directory not found (will be created on first link)"; \
	fi
	@echo ""
	@echo "Target MVS Dataset: $(LOADLIB)"
	@echo ""
	@echo "Link command: $(LD)"
	@if command -v $(LD) >/dev/null 2>&1; then \
		echo "  ✓ Linker available"; \
	else \
		echo "  ✗ Linker not found in PATH"; \
	fi
	@echo ""

# Dependency: stamps depend on object files
# If object file is newer than stamp, relink
$(ALL_STAMPS): $(LINK_STAMP_DIR)/%.stamp: $(OBJ_DIR)/%.o

# Made with Bob
