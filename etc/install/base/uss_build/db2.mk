# CBSA DB2 Management Makefile
# Manages DB2 database, tables, indexes, packages, and plans using db2cmd.py
# Copyright IBM Corp. 2023, 2025

.PHONY: db2-help db2-create db2-drop db2-bind-packages db2-bind-plan db2-bind-all \
        db2-create-database db2-create-stogroups db2-create-tablespaces \
        db2-create-tables db2-create-indexes db2-grant db2-test

# DB2 SQL directory
DB2SQL_DIR := $(mkfile_dir)/db2sql

# Configuration from build.conf
-include build.conf

# DB2 Configuration variables (with defaults)
DB2_HLQ ?= DSNC10
DB2_SUBSYSTEM ?= DBCG
DB2_OWNER ?= IBMUSER
DB2_PLAN ?= CBSA
DB2_PACKAGE ?= PCBSA
DB2_DSNTEP_PLAN ?= DSNTEP2
DB2_DSNTEP_LOADLIB ?= $(DB2_HLQ).RUNLIB.LOAD
DB2_VCAT ?= DSNV12DP
BANK_USER ?= CICSUSER

# db2cmd.py command
DB2CMD := $(mkfile_dir)/bin/db2cmd.py

# Helper function to substitute SQL variables using envsubst and execute db2cmd with named pipes
define run_db2cmd
	@echo "Executing $(1)..."
	@SYSTSIN_PIPE=/tmp/systsin_$(1)_$$$$.pipe; \
	SYSIN_PIPE=/tmp/sysin_$(1)_$$$$.pipe; \
	mkfifo $$SYSTSIN_PIPE $$SYSIN_PIPE; \
	export DB2_HLQ='$(DB2_HLQ)' \
	       DB2_SUBSYSTEM='$(DB2_SUBSYSTEM)' \
	       DB2_OWNER='$(DB2_OWNER)' \
	       BANK_PLAN='$(DB2_PLAN)' \
	       BANK_PACKAGE='$(DB2_PACKAGE)' \
	       DB2_DSNTEP_PLAN='$(DB2_DSNTEP_PLAN)' \
	       DB2_DSNTEP_LOADLIB='$(DB2_DSNTEP_LOADLIB)' \
	       DB2_VCAT='$(DB2_VCAT)' \
	       BANK_USER='$(BANK_USER)'; \
	(envsubst < $(DB2SQL_DIR)/systsin.template > $$SYSTSIN_PIPE &); \
	(envsubst < $(DB2SQL_DIR)/$(1).sql > $$SYSIN_PIPE &); \
	$(DB2CMD) --systsin $$SYSTSIN_PIPE --sysin $$SYSIN_PIPE; \
	rm -f $$SYSTSIN_PIPE $$SYSIN_PIPE
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
	@$(call run_db2cmd,CREDB00)
	@echo "✓ Database created"

# Create storage groups
db2-create-stogroups:
	@echo "Creating storage groups..."
	@$(call run_db2cmd,CRESG01)
	@$(call run_db2cmd,CRESG02)
	@$(call run_db2cmd,CRESG03)
	@echo "✓ Storage groups created"

# Create tablespaces
db2-create-tablespaces:
	@echo "Creating tablespaces..."
	@$(call run_db2cmd,CRETS01)
	@$(call run_db2cmd,CRETS02)
	@$(call run_db2cmd,CRETS03)
	@echo "✓ Tablespaces created"

# Create tables
db2-create-tables:
	@echo "Creating tables..."
	@$(call run_db2cmd,CRETB01)
	@$(call run_db2cmd,CRETB02)
	@$(call run_db2cmd,CRETB03)
	@echo "✓ Tables created"

# Create indexes
db2-create-indexes:
	@echo "Creating indexes..."
	@$(call run_db2cmd,CREI101)
	@$(call run_db2cmd,CREI201)
	@$(call run_db2cmd,CREI301)
	@echo "✓ Indexes created"

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
	@echo ""

# Rebuild DB2 (drop and recreate)
db2-rebuild: db2-drop db2-create db2-bind-all
	@echo "✓ DB2 rebuild complete"

# Made with Bob
