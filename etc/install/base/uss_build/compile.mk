# CBSA COBOL Compilation Makefile
# Handles incremental compilation of COBOL programs and BMS maps
# All source and object files are in USS (not MVS datasets)

# Include configuration
include build.conf

# Directories
SRC_DIR := ../../../src/base
COBOL_SRC_DIR := $(SRC_DIR)/cobol_src
BMS_SRC_DIR := $(SRC_DIR)/bms_src
COPY_DIR := $(SRC_DIR)/cobol_copy
BUILD_DIR := build
OBJ_DIR := $(BUILD_DIR)/obj
LOAD_DIR := $(BUILD_DIR)/load
DBRM_DIR := $(BUILD_DIR)/dbrm
DSECT_DIR := $(BUILD_DIR)/dsect

# Create build directories
$(shell mkdir -p $(OBJ_DIR) $(LOAD_DIR) $(DBRM_DIR) $(DSECT_DIR))

# COBOL Compiler
COBOL := cob2

# Compiler flags
COBOL_FLAGS := -c -q"RENT,APOST,NODYNAM,OPTIMIZE(FULL),TRUNC(STD)"
COBOL_CICS_FLAGS := -q"CICS('SP,EDF')"
COBOL_SQL_FLAGS := -q"SQL"
COBOL_INCLUDE := -I$(COPY_DIR) -I"//$(CICS_HLQ).SDFHCOB" -I"//$(DB2_HLQ).SDSNMACS"

# Linker
LINKER := cob2
LINK_FLAGS := -q"RENT,AMODE=31,RMODE=ANY"

# BMS Assembler (using CICS-provided utility)
BMS_ASM := dfhmsd
BMS_FLAGS := TYPE=DSECT,MODE=INOUT,LANG=COBOL,TIOAPFX=YES

# COBOL Programs (CICS + DB2)
CICS_DB2_PROGRAMS := \
	ABNDPROC \
	BNKMENU \
	CRDTAGY1 \
	CRDTAGY2 \
	CRDTAGY3 \
	CRDTAGY4 \
	CRDTAGY5 \
	CREACC \
	CRECUST \
	DBCRFUN \
	DELACC \
	DELCUS \
	GETCOMPY \
	GETSCODE \
	INQACC \
	INQACCCU \
	INQCUST \
	UPDACC \
	UPDCUST \
	XFRFUN \
	BNK1CAC \
	BNK1CCA \
	BNK1CCS \
	BNK1CRA \
	BNK1DAC \
	BNK1DCS \
	BNK1TFN \
	BNK1UAC

# Batch Programs (DB2 only, no CICS)
BATCH_PROGRAMS := \
	BANKDATA

# All programs
ALL_PROGRAMS := $(CICS_DB2_PROGRAMS) $(BATCH_PROGRAMS)

# BMS Maps
BMS_MAPS := \
	BNK1MAI \
	BNK1ACC \
	BNK1CAM \
	BNK1CCM \
	BNK1CDM \
	BNK1DAM \
	BNK1DCM \
	BNK1TFM \
	BNK1UAM

# Object files
CICS_DB2_OBJS := $(addprefix $(OBJ_DIR)/,$(addsuffix .o,$(CICS_DB2_PROGRAMS)))
BATCH_OBJS := $(addprefix $(OBJ_DIR)/,$(addsuffix .o,$(BATCH_PROGRAMS)))
ALL_OBJS := $(CICS_DB2_OBJS) $(BATCH_OBJS)

# Load modules
CICS_DB2_LOADS := $(addprefix $(LOAD_DIR)/,$(CICS_DB2_PROGRAMS))
BATCH_LOADS := $(addprefix $(LOAD_DIR)/,$(BATCH_PROGRAMS))
ALL_LOADS := $(CICS_DB2_LOADS) $(BATCH_LOADS)

# DBRM files
CICS_DB2_DBRMS := $(addprefix $(DBRM_DIR)/,$(addsuffix .dbrm,$(CICS_DB2_PROGRAMS)))
BATCH_DBRMS := $(addprefix $(DBRM_DIR)/,$(addsuffix .dbrm,$(BATCH_PROGRAMS)))
ALL_DBRMS := $(CICS_DB2_DBRMS) $(BATCH_DBRMS)

# BMS outputs
BMS_LOADS := $(addprefix $(LOAD_DIR)/,$(BMS_MAPS))
BMS_DSECTS := $(addprefix $(DSECT_DIR)/,$(addsuffix .cpy,$(BMS_MAPS)))

# Phony targets
.PHONY: all programs maps clean clean-obj clean-all help list-programs list-maps

# Default target
all: programs maps

# Help target
help:
	@echo "CBSA COBOL Compilation Makefile"
	@echo "================================"
	@echo ""
	@echo "Targets:"
	@echo "  all            - Compile all programs and assemble all maps (default)"
	@echo "  programs       - Compile all COBOL programs"
	@echo "  maps           - Assemble all BMS maps"
	@echo "  clean          - Remove all build artifacts"
	@echo "  clean-obj      - Remove object files only (keep load modules)"
	@echo "  list-programs  - List all programs to be compiled"
	@echo "  list-maps      - List all BMS maps to be assembled"
	@echo ""
	@echo "Individual program compilation:"
	@echo "  make $(LOAD_DIR)/<PROGRAM>    - Compile specific program"
	@echo ""
	@echo "Examples:"
	@echo "  make                          # Compile everything"
	@echo "  make programs                 # Compile programs only"
	@echo "  make $(LOAD_DIR)/CREACC       # Compile CREACC only"
	@echo "  make clean all                # Clean rebuild"
	@echo ""
	@echo "Build directories:"
	@echo "  Source:  $(COBOL_SRC_DIR)"
	@echo "  Objects: $(OBJ_DIR)"
	@echo "  Loads:   $(LOAD_DIR)"
	@echo "  DBRMs:   $(DBRM_DIR)"
	@echo ""

# List programs
list-programs:
	@echo "CICS+DB2 Programs ($(words $(CICS_DB2_PROGRAMS))):"
	@echo "$(CICS_DB2_PROGRAMS)" | tr ' ' '\n' | sed 's/^/  /'
	@echo ""
	@echo "Batch Programs ($(words $(BATCH_PROGRAMS))):"
	@echo "$(BATCH_PROGRAMS)" | tr ' ' '\n' | sed 's/^/  /'

# List maps
list-maps:
	@echo "BMS Maps ($(words $(BMS_MAPS))):"
	@echo "$(BMS_MAPS)" | tr ' ' '\n' | sed 's/^/  /'

# Compile all programs
programs: $(ALL_LOADS)
	@echo ""
	@echo "✓ All programs compiled successfully"
	@echo "  Load modules: $(LOAD_DIR)/"

# Assemble all maps
maps: $(BMS_LOADS) $(BMS_DSECTS)
	@echo ""
	@echo "✓ All BMS maps assembled successfully"
	@echo "  Load modules: $(LOAD_DIR)/"
	@echo "  DSECTs:       $(DSECT_DIR)/"

# Pattern rule for CICS+DB2 programs (compile and link)
$(LOAD_DIR)/%: $(OBJ_DIR)/%.o | $(LOAD_DIR)
	@echo "Linking $*..."
	@$(LINKER) $(LINK_FLAGS) -o $@ $<
	@echo "✓ $* linked successfully"

# Pattern rule for CICS+DB2 object files
$(OBJ_DIR)/%.o: $(COBOL_SRC_DIR)/%.cbl | $(OBJ_DIR) $(DBRM_DIR)
	@echo "Compiling $* (CICS+DB2)..."
	@$(COBOL) $(COBOL_FLAGS) $(COBOL_CICS_FLAGS) $(COBOL_SQL_FLAGS) \
		$(COBOL_INCLUDE) \
		-o $@ \
		-qdbrm=$(DBRM_DIR)/$*.dbrm \
		$<
	@echo "✓ $* compiled successfully"

# Special rule for batch programs (DB2 only, no CICS)
$(OBJ_DIR)/BANKDATA.o: $(COBOL_SRC_DIR)/BANKDATA.cbl | $(OBJ_DIR) $(DBRM_DIR)
	@echo "Compiling BANKDATA (Batch+DB2)..."
	@$(COBOL) $(COBOL_FLAGS) $(COBOL_SQL_FLAGS) \
		$(COBOL_INCLUDE) \
		-o $@ \
		-qdbrm=$(DBRM_DIR)/BANKDATA.dbrm \
		$<
	@echo "✓ BANKDATA compiled successfully"

# Pattern rule for BMS map assembly (load module)
$(LOAD_DIR)/%: $(BMS_SRC_DIR)/%.bms | $(LOAD_DIR)
	@echo "Assembling BMS map $* (load module)..."
	@$(BMS_ASM) $(BMS_FLAGS),TYPE=MAP -o $@ $<
	@echo "✓ $* map assembled successfully"

# Pattern rule for BMS DSECT generation
$(DSECT_DIR)/%.cpy: $(BMS_SRC_DIR)/%.bms | $(DSECT_DIR)
	@echo "Generating DSECT for $*..."
	@$(BMS_ASM) $(BMS_FLAGS),TYPE=DSECT -o $@ $<
	@echo "✓ $* DSECT generated successfully"

# Create directories
$(OBJ_DIR) $(LOAD_DIR) $(DBRM_DIR) $(DSECT_DIR):
	@mkdir -p $@

# Clean targets
clean-obj:
	@echo "Removing object files..."
	@rm -rf $(OBJ_DIR)
	@echo "✓ Object files removed"

clean:
	@echo "Removing all build artifacts..."
	@rm -rf $(BUILD_DIR)
	@echo "✓ Build directory removed"

clean-all: clean

# Dependency tracking for copybooks
# Programs depend on their copybooks
$(OBJ_DIR)/ABNDPROC.o: $(COPY_DIR)/ABNDINFO.cpy
$(OBJ_DIR)/CREACC.o: $(COPY_DIR)/CREACC.cpy
$(OBJ_DIR)/CRECUST.o: $(COPY_DIR)/CRECUST.cpy
$(OBJ_DIR)/DELACC.o: $(COPY_DIR)/DELACC.cpy
$(OBJ_DIR)/DELCUS.o: $(COPY_DIR)/DELCUS.cpy
$(OBJ_DIR)/INQACC.o: $(COPY_DIR)/INQACC.cpy
$(OBJ_DIR)/INQACCCU.o: $(COPY_DIR)/INQACCCU.cpy
$(OBJ_DIR)/INQCUST.o: $(COPY_DIR)/INQCUST.cpy
$(OBJ_DIR)/UPDACC.o: $(COPY_DIR)/UPDACC.cpy
$(OBJ_DIR)/UPDCUST.o: $(COPY_DIR)/UPDCUST.cpy

# Programs that depend on BMS DSECTs
$(OBJ_DIR)/BNK1CAC.o: $(DSECT_DIR)/BNK1CAM.cpy
$(OBJ_DIR)/BNK1CCA.o: $(DSECT_DIR)/BNK1CCM.cpy
$(OBJ_DIR)/BNK1CCS.o: $(DSECT_DIR)/BNK1CDM.cpy
$(OBJ_DIR)/BNK1CRA.o: $(DSECT_DIR)/BNK1MAI.cpy
$(OBJ_DIR)/BNK1DAC.o: $(DSECT_DIR)/BNK1DAM.cpy
$(OBJ_DIR)/BNK1DCS.o: $(DSECT_DIR)/BNK1DCM.cpy
$(OBJ_DIR)/BNK1TFN.o: $(DSECT_DIR)/BNK1TFM.cpy
$(OBJ_DIR)/BNK1UAC.o: $(DSECT_DIR)/BNK1UAM.cpy
$(OBJ_DIR)/BNKMENU.o: $(DSECT_DIR)/BNK1MAI.cpy

# Show build status
status:
	@echo "Build Status"
	@echo "============"
	@echo ""
	@echo "Source files:"
	@echo "  COBOL programs: $(words $(wildcard $(COBOL_SRC_DIR)/*.cbl))"
	@echo "  BMS maps:       $(words $(wildcard $(BMS_SRC_DIR)/*.bms))"
	@echo "  Copybooks:      $(words $(wildcard $(COPY_DIR)/*.cpy))"
	@echo ""
	@echo "Build artifacts:"
	@echo "  Object files:   $(words $(wildcard $(OBJ_DIR)/*.o))"
	@echo "  Load modules:   $(words $(wildcard $(LOAD_DIR)/*))"
	@echo "  DBRMs:          $(words $(wildcard $(DBRM_DIR)/*.dbrm))"
	@echo "  DSECTs:         $(words $(wildcard $(DSECT_DIR)/*.cpy))"
	@echo ""

# Parallel compilation support
.NOTPARALLEL: maps

# Made with Bob
