# CBSA COBOL Compilation Makefile
# Incremental compilation using COBCC compiler interface in USS
# Use the bash shell and if a command in a pipe fails, fail immediately.

.PHONY: clean-cobol help-cobol list-programs status-cobol

# Note: Common variables (SRC_DIR, COPY_DIR, BUILD_DIR, OBJ_DIR)
# are defined in the main Makefile

# Compiler settings
COBCC := cobcc
COBOL_FLAGS := -comprc_ok=4 -qrent -qlist -qxref -qmap -qapost
CICS_FLAGS := -qcics -q'COPYLOC(DSN(CICSTS62.CICS.SDFHCOB))' -q'COPYLOC(DSN(CEE.SCEESAMP))'
DB2_FLAGS := -q"sql('CCSID(1140)')" -q'codepage(1140)' -dbrmlib

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
CICS_LOADS := $(addprefix $(LOAD_DIR)/,$(addsuffix .exe,$(CICS_PROGRAMS)))
BATCH_LOADS := $(addprefix $(LOAD_DIR)/,$(addsuffix .exe,$(BATCH_PROGRAMS)))
ALL_LOADS := $(CICS_LOADS) $(BATCH_LOADS)

# Target for compiling all COBOL programs (called from main Makefile)
cobol-programs: $(ALL_OBJS) $(ALL_LOADS)
	@echo "COBOL compilation complete: $(words $(ALL_LOADS)) programs built"

# Create build directories
$(OBJ_DIR) $(LOAD_DIR):
	@mkdir -p $@

# Compile CICS programs (with CICS and DB2 support)
# The 'cat' at the end is to ensure that the errors are tagged as IBM-1047
# DB2 compilation notes:
# - Remove any existing symbolic link before compilation to ensure clean state
# - After successful compilation, create symbolic link from program name to .dbrm file
#   (e.g., CREACC -> CREACC.dbrm) so db2bind can reference members without extension

$(OBJ_DIR)/%.o: $(SRC_DIR)/%.cbl
	@echo "Compiling CICS program: $*"
	@rm -f $(OBJ_DIR)/$*
	( \
		cd $(OBJ_DIR); \
		$(COBCC) $(COBOL_FLAGS) $(CICS_FLAGS) $(DB2_FLAGS) \
		-I$(abspath $(COPY_DIR)) -I$(abspath $(BMS_MACRO_DIR)) \
		-c \
		$(abspath $<) \
	) && ln -sf $*.dbrm $(OBJ_DIR)/$* || true
	@echo "$* compiled successfully"

# Compile batch programs (no CICS, with DB2 support)
# DB2 compilation notes:
# - Remove any existing symbolic link before compilation to ensure clean state
# - After successful compilation, create symbolic link from program name to .dbrm file
#   (e.g., BANKDATA -> BANKDATA.dbrm) so db2bind can reference members without extension
$(OBJ_DIR)/BANKDATA.o: $(SRC_DIR)/BANKDATA.cbl
	@echo "Compiling batch program: BANKDATA"
	@rm -f $(OBJ_DIR)/BANKDATA
	( \
		cd $(OBJ_DIR); \
		$(COBCC) $(COBOL_FLAGS) $(DB2_FLAGS) \
		-I$(abspath $(COPY_DIR)) -I$(abspath $(BMS_MACRO_DIR)) \
		-c \
		$(abspath $<) \
	) && ln -sf BANKDATA.dbrm $(OBJ_DIR)/BANKDATA || true
	@echo "BANKDATA compiled successfully"

$(LOAD_DIR)/%.exe : $(OBJ_DIR)/%.o
	@echo "Binding load module: $*"
	( \
		cd $(LOAD_DIR); \
		$(LD) $(LD_FLAGS) -o $*.exe $(abspath $<) \
	)
	@echo "$* bound successfully"

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
	@echo "Available targets:"
	@echo "  cobol-programs   - Compile all programs"
	@echo "  clean-cobol      - Remove build artifacts"
	@echo "  list-programs    - List all programs"
	@echo "  status-cobol     - Show build status"
	@echo ""
	@echo "Examples:"
	@echo "  gmake cobol-programs              # Compile all programs"
	@echo "  gmake $(LOAD_DIR)/CREACC.exe      # Compile CREACC only"
	@echo "  gmake -j4 cobol-programs          # Compile with 4 parallel jobs"
	@echo "  gmake clean-cobol cobol-programs  # Clean and rebuild all"
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
	@echo ""
	@echo "Note: DBRM files are generated in $(OBJ_DIR) with symbolic links"
	@echo "      for db2bind compatibility (e.g., CREACC -> CREACC.dbrm)"
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
	else \
		echo "  ✗ Build directory not found (will be created on first build)"; \
	fi
	@echo ""
	@echo "Compiler: $(COBCC)"
	@if command -v $(COBCC) >/dev/null 2>&1; then \
		echo "  ✓ Compiler available"; \
	else \
		echo "  ✗ Compiler not found in PATH"; \
	fi
	@echo ""
 
 