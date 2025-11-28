# CBSA BMS Map Assembly Makefile
# Incremental assembly using as command in USS
# Copyright IBM Corp. 2023, 2025

.PHONY: clean-assemble help-assemble list-maps status-assemble

# Note: Common variables (BMS_SRC_DIR, BUILD_DIR, OBJ_DIR, DSECT_DIR,
# LOADLIB_HLQ, LOADLIB, DSECT_LIB) are defined in the main Makefile

# Assembly-specific directories
BMS_MACRO_DIR := $(BUILD_DIR)/bmsmac
BMS_OBJ_DIR := $(BUILD_DIR)/bmsobj

# Assembler settings
AS := as
AS_FLAGS := -mgoff

# BMS maps (from buildjcl directory analysis)
BMS_MAPS := BNK1ACC BNK1CAM BNK1CCM BNK1CDM BNK1DAM BNK1DCM BNK1MAI BNK1TFM BNK1UAM

# Object files for maps
MAP_OBJS := $(addprefix $(BMS_OBJ_DIR)/,$(addsuffix .o,$(BMS_MAPS)))

# Generated COPYBOOK files
MAP_MACROS := $(addprefix $(BMS_MACRO_DIR)/,$(addsuffix .cpy,$(BMS_MAPS)))

# Create assembly directories
$(BMS_MACRO_DIR) $(BMS_OBJ_DIR):
	mkdir -p $@

# Target for assembling all maps
assemble-maps: $(MAP_MACROS)
	@echo "✓ BMS map assembly complete: $(words $(MAP_MACROS)) maps assembled"

# Assemble BMS maps
# Process: .bms -> assemble MAP -> link to LOADLIB, assemble DSECT -> copy to DSECT dataset
$(BMS_MACRO_DIR)/%.cpy: $(BMS_SRC_DIR)/%.bms 
	@echo "Assembling BMS map: $*"
	@# Step 1: Generate MAP assembler source
	@#echo "  Generating MAP source..."
	@#cicsbms -m $< -o $(ASSEMBLE_DIR)/$*.map.asm -t MAP
	@# Step 2: Assemble MAP to object
	@#echo "  Assembling MAP..."
	@#$(AS) $(AS_FLAGS) -o $(OBJ_DIR)/$*.o $(ASSEMBLE_DIR)/$*.map.asm
	@# Step 3: Link MAP object to LOADLIB
	@#echo "  Linking MAP to $(LOADLIB)($*)..."
	@#ld -b rent -b case=mixed -e $* -o "//$(LOADLIB)($*)" $(OBJ_DIR)/$*.o
	@# Step 4: Generate DSECT assembler source
	@echo "  Generating Copy Book..."
	as --'SYSPARM(DSECT)' -I"CICSTS62.CICS.SDFHMAC" -o $@.oneline $(BMS_SRC_DIR)/$*.bms || [ $$? -le 4 ]
	fold <$@.oneline | iconv -T -f ISO8859-1 -t IBM-1047 >$@
	rm $@.oneline
	@#cicsbms -m $< -o $(ASSEMBLE_DIR)/$*.dsect.asm -t DSECT
	@# Step 5: Assemble DSECT to copybook
	@#echo "  Assembling DSECT..."
	@#$(AS) $(AS_FLAGS) -o $(DSECT_DIR)/$*.cpy $(ASSEMBLE_DIR)/$*.dsect.asm
	@# Step 6: Copy DSECT to MVS dataset
	@#echo "  Copying DSECT to $(DSECT_LIB)($*)..."
	@#cp -F rec $(DSECT_DIR)/$*.cpy "//$(DSECT_LIB)($*)"
	@#touch $@
	@echo "$* assembled successfully"

# Clean assembly artifacts
clean-assemble:
	@echo "Cleaning BMS assembly artifacts..."
	@rm -rf $(ASSEMBLE_DIR)
	@echo "✓ Assembly clean complete"

# Help target
help-assemble:
	@echo "CBSA BMS Map Assembly Makefile"
	@echo "=============================="
	@echo ""
	@echo "Usage:"
	@echo "  make assemble-maps              - Assemble all BMS maps"
	@echo "  make $(BMS_MACRO_DIR)/<MAP>.stamp - Assemble specific map"
	@echo "  make clean-assemble             - Remove assembly artifacts"
	@echo "  make list-maps                  - List all BMS maps"
	@echo "  make status-assemble            - Show assembly status"
	@echo ""
	@echo "Examples:"
	@echo "  make assemble-maps                      # Assemble all maps"
	@echo "  make $(BMS_MACRO_DIR)/BNK1ACC.stamp # Assemble BNK1ACC only"
	@echo "  make -j4 assemble-maps                  # Assemble with 4 parallel jobs"
	@echo "  make clean-assemble assemble-maps       # Clean and reassemble all"
	@echo ""
	@echo "BMS Maps: $(words $(BMS_MAPS))"
	@echo ""
	@echo "Target MVS Datasets:"
	@echo "  Load modules: $(LOADLIB)"
	@echo "  DSECTs: $(DSECT_LIB)"
	@echo ""
	@echo "Note: Stamp files in $(BMS_MACRO_DIR) track assembly status"
	@echo ""

# List all maps
list-maps:
	@echo "BMS Maps ($(words $(BMS_MAPS))):"
	@for map in $(BMS_MAPS); do echo "  $$map"; done
	@echo ""
	@echo "Total: $(words $(BMS_MAPS)) maps"

# Show assembly status
status-assemble:
	@echo "BMS Assembly Status"
	@echo "==================="
	@echo ""
	@echo "BMS source directory: $(BMS_SRC_DIR)"
	@if [ -d "$(BMS_SRC_DIR)" ]; then \
		echo "  ✓ BMS source directory exists"; \
		echo "  Files: $$(ls -1 $(BMS_SRC_DIR)/*.bms 2>/dev/null | wc -l)"; \
	else \
		echo "  ✗ BMS source directory not found"; \
	fi
	@echo ""
	@echo "Object directory: $(OBJ_DIR)"
	@if [ -d "$(OBJ_DIR)" ]; then \
		echo "  ✓ Object directory exists"; \
		echo "  Map objects: $$(ls -1 $(OBJ_DIR)/*.o 2>/dev/null | wc -l)"; \
	else \
		echo "  ✗ Object directory not found"; \
	fi
	@echo ""
	@echo "DSECT directory: $(DSECT_DIR)"
	@if [ -d "$(DSECT_DIR)" ]; then \
		echo "  ✓ DSECT directory exists"; \
		echo "  DSECTs: $$(ls -1 $(DSECT_DIR)/*.cpy 2>/dev/null | wc -l)"; \
	else \
		echo "  ✗ DSECT directory not found"; \
	fi
	@echo ""
	@echo "Assembly stamp directory: $(BMS_MACRO_DIR)"
	@if [ -d "$(BMS_MACRO_DIR)" ]; then \
		echo "  ✓ Stamp directory exists"; \
		echo "  Stamps: $$(ls -1 $(BMS_MACRO_DIR)/*.stamp 2>/dev/null | wc -l)"; \
	else \
		echo "  ✗ Stamp directory not found (will be created on first assembly)"; \
	fi
	@echo ""
	@echo "Target MVS Datasets:"
	@echo "  Load modules: $(LOADLIB)"
	@echo "  DSECTs: $(DSECT_LIB)"
	@echo ""
	@echo "Assembler: $(AS)"
	@if command -v $(AS) >/dev/null 2>&1; then \
		echo "  ✓ Assembler available"; \
	else \
		echo "  ✗ Assembler not found in PATH"; \
	fi
	@echo ""
	@echo "CICS BMS utility: cicsbms"
	@if command -v cicsbms >/dev/null 2>&1; then \
		echo "  ✓ cicsbms available"; \
	else \
		echo "  ✗ cicsbms not found in PATH"; \
	fi
	@echo ""

