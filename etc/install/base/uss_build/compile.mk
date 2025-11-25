# CBSA COBOL Compilation Makefile
# Incremental compilation using cob2 compiler interface in USS
# Copyright IBM Corp. 2023, 2025

.PHONY: clean-cobol help-cobol list-programs status-cobol

# Note: Common variables (SRC_DIR, COPY_DIR, BUILD_DIR, OBJ_DIR, DBRM_DIR)
# are defined in the main Makefile

# Compiler settings
COB2 := cob2
COBOL_FLAGS := -qrent -qlist -qxref -qmap -qopt -qapost -qtrunc=opt
CICS_FLAGS := -qcics
DB2_FLAGS := -qsql

# COBOL source files (from cobol_src.md analysis)
CICS_PROGRAMS := ABNDPROC BNK1CAC BNK1CCA BNK1CCS BNK1CRA BNK1DAC BNK1DCS \
                 BNK1TFN BNK1UAC BNKMENU CRDTAGY1 CRDTAGY2 CRDTAGY3 CRDTAGY4 \
                 CRDTAGY5 CREACC CRECUST DBCRFUN DELACC DELCUS GETCOMPY \
                 GETSCODE INQACC INQACCCU INQCUST UPDACC UPDCUST XFRFUN

BATCH_PROGRAMS := BANKDATA

# All programs
ALL_PROGRAMS := $(CICS_PROGRAMS) $(BATCH_PROGRAMS)

# Object files
CICS_OBJS := $(addprefix $(OBJ_DIR)/,$(addsuffix .o,$(CICS_PROGRAMS)))
BATCH_OBJS := $(addprefix $(OBJ_DIR)/,$(addsuffix .o,$(BATCH_PROGRAMS)))
ALL_OBJS := $(CICS_OBJS) $(BATCH_OBJS)

# Load modules
CICS_LOADS := $(addprefix $(LOAD_DIR)/,$(CICS_PROGRAMS))
BATCH_LOADS := $(addprefix $(LOAD_DIR)/,$(BATCH_PROGRAMS))
ALL_LOADS := $(CICS_LOADS) $(BATCH_LOADS)

# Target for compiling all COBOL programs (called from main Makefile)
cobol-programs: $(ALL_LOADS)
	@echo "✓ COBOL compilation complete: $(words $(ALL_LOADS)) programs built"

# Create build directories
$(OBJ_DIR) $(LOAD_DIR) $(DBRM_DIR):
	@mkdir -p $@

# Compile CICS programs (with CICS and DB2 support)
$(LOAD_DIR)/%: $(SRC_DIR)/%.cbl | $(OBJ_DIR) $(LOAD_DIR) $(DBRM_DIR)
	@echo "Compiling CICS program: $*"
	@$(COB2) $(COBOL_FLAGS) $(CICS_FLAGS) $(DB2_FLAGS) \
		-I$(COPY_DIR) \
		-o $@ \
		-c -qOBJECT=$(OBJ_DIR)/$*.o \
		-qDBRM=$(DBRM_DIR)/$*.dbrm \
		$<
	@echo "✓ $* compiled successfully"

# Compile batch programs (no CICS, with DB2 support)
$(LOAD_DIR)/BANKDATA: $(SRC_DIR)/BANKDATA.cbl | $(OBJ_DIR) $(LOAD_DIR) $(DBRM_DIR)
	@echo "Compiling batch program: BANKDATA"
	@$(COB2) $(COBOL_FLAGS) $(DB2_FLAGS) \
		-I$(COPY_DIR) \
		-o $@ \
		-c -qOBJECT=$(OBJ_DIR)/BANKDATA.o \
		-qDBRM=$(DBRM_DIR)/BANKDATA.dbrm \
		$<
	@echo "✓ BANKDATA compiled successfully"

# Clean build artifacts
clean-cobol:
	@echo "Cleaning COBOL build artifacts..."
	@rm -rf $(BUILD_DIR)
	@echo "✓ COBOL clean complete"

# Help target
help-cobol:
	@echo "CBSA COBOL Compilation Makefile"
	@echo "================================"
	@echo ""
	@echo "Usage:"
	@echo "  make cobol-programs     - Compile all programs"
	@echo "  make $(LOAD_DIR)/<PROG> - Compile specific program"
	@echo "  make clean-cobol        - Remove build artifacts"
	@echo "  make list-programs      - List all programs"
	@echo "  make status-cobol       - Show build status"
	@echo ""
	@echo "Examples:"
	@echo "  make cobol-programs            # Compile all programs"
	@echo "  make $(LOAD_DIR)/CREACC        # Compile CREACC only"
	@echo "  make -j4 cobol-programs        # Compile with 4 parallel jobs"
	@echo "  make clean-cobol cobol-programs # Clean and rebuild all"
	@echo ""
	@echo "Programs:"
	@echo "  CICS Programs: $(words $(CICS_PROGRAMS))"
	@echo "  Batch Programs: $(words $(BATCH_PROGRAMS))"
	@echo "  Total: $(words $(ALL_PROGRAMS))"
	@echo ""
	@echo "Build directories:"
	@echo "  Source:  $(SRC_DIR)"
	@echo "  Copy:    $(COPY_DIR)"
	@echo "  Objects: $(OBJ_DIR)"
	@echo "  Loads:   $(LOAD_DIR)"
	@echo "  DBRMs:   $(DBRM_DIR)"
	@echo ""

# List all programs
list-programs:
	@echo "CICS Programs ($(words $(CICS_PROGRAMS))):"
	@for prog in $(CICS_PROGRAMS); do echo "  $$prog"; done
	@echo ""
	@echo "Batch Programs ($(words $(BATCH_PROGRAMS))):"
	@for prog in $(BATCH_PROGRAMS); do echo "  $$prog"; done
	@echo ""
	@echo "Total: $(words $(ALL_PROGRAMS)) programs"

# Show build status
status-cobol:
	@echo "Build Status"
	@echo "============"
	@echo ""
	@echo "Source directory: $(SRC_DIR)"
	@if [ -d "$(SRC_DIR)" ]; then \
		echo "  ✓ Source directory exists"; \
		echo "  Files: $$(ls -1 $(SRC_DIR)/*.cbl 2>/dev/null | wc -l)"; \
	else \
		echo "  ✗ Source directory not found"; \
	fi
	@echo ""
	@echo "Copy directory: $(COPY_DIR)"
	@if [ -d "$(COPY_DIR)" ]; then \
		echo "  ✓ Copy directory exists"; \
		echo "  Files: $$(ls -1 $(COPY_DIR)/*.cpy 2>/dev/null | wc -l)"; \
	else \
		echo "  ✗ Copy directory not found"; \
	fi
	@echo ""
	@echo "Build directory: $(BUILD_DIR)"
	@if [ -d "$(BUILD_DIR)" ]; then \
		echo "  ✓ Build directory exists"; \
		if [ -d "$(OBJ_DIR)" ]; then \
			echo "  Objects: $$(ls -1 $(OBJ_DIR)/*.o 2>/dev/null | wc -l)"; \
		fi; \
		if [ -d "$(LOAD_DIR)" ]; then \
			echo "  Loads: $$(ls -1 $(LOAD_DIR) 2>/dev/null | wc -l)"; \
		fi; \
		if [ -d "$(DBRM_DIR)" ]; then \
			echo "  DBRMs: $$(ls -1 $(DBRM_DIR)/*.dbrm 2>/dev/null | wc -l)"; \
		fi; \
	else \
		echo "  ✗ Build directory not found (will be created on first build)"; \
	fi
	@echo ""
	@echo "Compiler: $(COB2)"
	@if command -v $(COB2) >/dev/null 2>&1; then \
		echo "  ✓ Compiler available"; \
	else \
		echo "  ✗ Compiler not found in PATH"; \
	fi
	@echo ""

# Dependency tracking (simplified - assumes all programs depend on all copybooks)
# For more sophisticated dependency tracking, consider using makedepend or similar
$(ALL_LOADS): $(wildcard $(COPY_DIR)/*.cpy)

# Made with Bob
