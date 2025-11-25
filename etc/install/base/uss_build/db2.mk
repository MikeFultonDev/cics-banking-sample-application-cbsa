# CBSA DB2 Management Makefile
# Manages DB2 database, tables, indexes, packages, and plans using JCL submission
# Copyright IBM Corp. 2023, 2025

.PHONY: db2-help db2-create db2-drop db2-bind-packages db2-bind-plan db2-bind-all \
        db2-create-database db2-create-stogroups db2-create-tablespaces \
        db2-create-tables db2-create-indexes db2-grant db2-test

# DB2 JCL directory
DB2JCL_DIR := ../db2jcl

# Configuration from build.conf
-include build.conf

# DB2 Configuration variables (with defaults)
DB2_HLQ ?= DSNC10
DB2_SUBSYSTEM ?= DBCG
DB2_OWNER ?= IBMUSER
DB2_PLAN ?= CBSA
DB2_PACKAGE ?= PCBSA
DB2_DSNTEP_PLAN ?= DSNTEP2
DB2_DSNTEP_LOADLIB ?= $(DB2_HLQ).RUNLIB
DB2_VCAT ?= DSNV12DP
BANK_USER ?= CICSUSER
DBRM ?= $(BANK_PREFIX).DBRM

# JCL submission command using ZOAU
SUBMIT_JCL := mvscmd --pgm=IEBGENER --sysut2=INTRDR

# Helper function to substitute JCL variables
define substitute_jcl
	@sed -e 's/@DB2_HLQ@/$(DB2_HLQ)/g' \
	     -e 's/@DB2_SUBSYSTEM@/$(DB2_SUBSYSTEM)/g' \
	     -e 's/@DB2_OWNER@/$(DB2_OWNER)/g' \
	     -e 's/@BANK_DBRMLIB@/$(DBRM)/g' \
	     -e 's/@BANK_PLAN@/$(DB2_PLAN)/g' \
	     -e 's/@BANK_PACKAGE@/$(DB2_PACKAGE)/g' \
	     -e 's/@DB2_DSNTEP_PLAN@/$(DB2_DSNTEP_PLAN)/g' \
	     -e 's/@DB2_DSNTEP_LOADLIB@/$(DB2_DSNTEP_LOADLIB)/g' \
	     -e 's/@BANK_USER@/$(BANK_USER)/g' \
	     $(1)
endef

# DB2 Help
db2-help:
	@echo "CBSA DB2 Management Targets"
	@echo "============================"
	@echo ""
	@echo "Database Creation:"
	@echo "  db2-create           - Create all DB2 artifacts (database, tables, indexes)"
	@echo "  db2-create-database  - Create CBSA database only"
	@echo "  db2-create-stogroups - Create storage groups only"
	@echo "  db2-create-tablespaces - Create tablespaces only"
	@echo "  db2-create-tables    - Create tables only"
	@echo "  db2-create-indexes   - Create indexes only"
	@echo ""
	@echo "DB2 Binding:"
	@echo "  db2-bind-all         - Bind packages and plan"
	@echo "  db2-bind-packages    - Bind DB2 packages only"
	@echo "  db2-bind-plan        - Bind DB2 plan only"
	@echo "  db2-grant            - Grant permissions to BANK_USER"
	@echo ""
	@echo "Database Cleanup:"
	@echo "  db2-drop             - Drop all DB2 artifacts"
	@echo ""
	@echo "Testing:"
	@echo "  db2-test             - Test DB2 connection with sample query"
	@echo ""
	@echo "Configuration Variables:"
	@echo "  DB2_HLQ=$(DB2_HLQ)"
	@echo "  DB2_SUBSYSTEM=$(DB2_SUBSYSTEM)"
	@echo "  DB2_OWNER=$(DB2_OWNER)"
	@echo "  DB2_PLAN=$(DB2_PLAN)"
	@echo "  DB2_PACKAGE=$(DB2_PACKAGE)"
	@echo "  BANK_USER=$(BANK_USER)"
	@echo ""

# Create all DB2 artifacts using INSTDB2.jcl
db2-create: db2-create-database db2-create-stogroups db2-create-tablespaces \
            db2-create-tables db2-create-indexes
	@echo "✓ All DB2 artifacts created successfully"

# Create database
db2-create-database:
	@echo "Creating CBSA database..."
	@$(call substitute_jcl,$(DB2JCL_DIR)/CREDB00.jcl) | $(SUBMIT_JCL)
	@echo "✓ Database creation job submitted"

# Create storage groups
db2-create-stogroups:
	@echo "Creating storage groups..."
	@$(call substitute_jcl,$(DB2JCL_DIR)/CRESG01.jcl) | $(SUBMIT_JCL)
	@$(call substitute_jcl,$(DB2JCL_DIR)/CRESG02.jcl) | $(SUBMIT_JCL)
	@$(call substitute_jcl,$(DB2JCL_DIR)/CRESG03.jcl) | $(SUBMIT_JCL)
	@echo "✓ Storage group creation jobs submitted"

# Create tablespaces
db2-create-tablespaces:
	@echo "Creating tablespaces..."
	@$(call substitute_jcl,$(DB2JCL_DIR)/CRETS01.jcl) | $(SUBMIT_JCL)
	@$(call substitute_jcl,$(DB2JCL_DIR)/CRETS02.jcl) | $(SUBMIT_JCL)
	@$(call substitute_jcl,$(DB2JCL_DIR)/CRETS03.jcl) | $(SUBMIT_JCL)
	@echo "✓ Tablespace creation jobs submitted"

# Create tables
db2-create-tables:
	@echo "Creating tables..."
	@$(call substitute_jcl,$(DB2JCL_DIR)/CRETB01.jcl) | $(SUBMIT_JCL)
	@$(call substitute_jcl,$(DB2JCL_DIR)/CRETB02.jcl) | $(SUBMIT_JCL)
	@$(call substitute_jcl,$(DB2JCL_DIR)/CRETB03.jcl) | $(SUBMIT_JCL)
	@echo "✓ Table creation jobs submitted"

# Create indexes
db2-create-indexes:
	@echo "Creating indexes..."
	@$(call substitute_jcl,$(DB2JCL_DIR)/CREI101.jcl) | $(SUBMIT_JCL)
	@$(call substitute_jcl,$(DB2JCL_DIR)/CREI201.jcl) | $(SUBMIT_JCL)
	@$(call substitute_jcl,$(DB2JCL_DIR)/CREI301.jcl) | $(SUBMIT_JCL)
	@echo "✓ Index creation jobs submitted"

# Bind all packages and plan
db2-bind-all: db2-bind-packages db2-bind-plan db2-grant
	@echo "✓ DB2 binding complete"

# Bind DB2 packages
db2-bind-packages:
	@echo "Binding DB2 packages..."
	@$(call substitute_jcl,$(DB2JCL_DIR)/DB2BIND.jcl) | $(SUBMIT_JCL)
	@echo "✓ Package binding job submitted"

# Bind DB2 plan (requires packages to exist)
db2-bind-plan:
	@echo "Binding DB2 plan..."
	@$(call substitute_jcl,$(DB2JCL_DIR)/DB2BIND.jcl) | $(SUBMIT_JCL)
	@echo "✓ Plan binding job submitted"

# Grant permissions
db2-grant:
	@echo "Granting permissions to $(BANK_USER)..."
	@$(call substitute_jcl,$(DB2JCL_DIR)/DB2BIND.jcl) | $(SUBMIT_JCL)
	@echo "✓ Grant job submitted"

# Drop all DB2 artifacts
db2-drop:
	@echo "Dropping all DB2 artifacts..."
	@$(call substitute_jcl,$(DB2JCL_DIR)/DROPDB2.jcl) | $(SUBMIT_JCL)
	@echo "✓ Drop job submitted"
	@echo "⚠ Warning: This will delete all CBSA database objects"

# Test DB2 connection
db2-test:
	@echo "Testing DB2 connection..."
	@$(call substitute_jcl,$(DB2JCL_DIR)/BTCHSQL.jcl) | $(SUBMIT_JCL)
	@echo "✓ Test query job submitted"

# Alternative: Create everything using single INSTDB2.jcl
db2-install-single:
	@echo "Creating all DB2 artifacts using INSTDB2.jcl..."
	@$(call substitute_jcl,$(DB2JCL_DIR)/INSTDB2.jcl) | $(SUBMIT_JCL)
	@echo "✓ Installation job submitted"
	@echo "Note: This creates database, storage groups, tablespaces, tables, and indexes"

# Show current DB2 configuration
db2-show-config:
	@echo "Current DB2 Configuration:"
	@echo "=========================="
	@echo "DB2_HLQ:           $(DB2_HLQ)"
	@echo "DB2_SUBSYSTEM:     $(DB2_SUBSYSTEM)"
	@echo "DB2_OWNER:         $(DB2_OWNER)"
	@echo "DB2_PLAN:          $(DB2_PLAN)"
	@echo "DB2_PACKAGE:       $(DB2_PACKAGE)"
	@echo "DB2_DSNTEP_PLAN:   $(DB2_DSNTEP_PLAN)"
	@echo "DB2_DSNTEP_LOADLIB: $(DB2_DSNTEP_LOADLIB)"
	@echo "DB2_VCAT:          $(DB2_VCAT)"
	@echo "BANK_USER:         $(BANK_USER)"
	@echo "DBRM:              $(DBRM)"
	@echo ""

# Rebuild DB2 (drop and recreate)
db2-rebuild: db2-drop db2-create db2-bind-all
	@echo "✓ DB2 rebuild complete"

# Made with Bob
