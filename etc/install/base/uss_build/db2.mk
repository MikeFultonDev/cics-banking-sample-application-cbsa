# CBSA DB2 Management Makefile
# Manages DB2 database, tables, indexes, packages, and plans using batchtsocmd package
# Copyright IBM Corp. 2023, 2025

.PHONY: db2-help db2-create db2-drop db2-bind-packages db2-bind-plan db2-bind-all \
        db2-create-database db2-create-stogroups db2-create-tablespaces \
        db2-create-tables db2-create-indexes db2-grant db2-test

# DB2 SQL and grant directories
DB2SQL_DIR := $(mkfile_dir)/db2sql
DB2GRANT_DIR := $(mkfile_dir)/db2grant

# Configuration from build.conf (BUILD_CONFIG is defined in parent Makefile)
-include build.conf

# Python script for DB2 operations
DB2_RUN := $(PYTHON) $(mkfile_dir)/db2_run.py

# Verbose flag
VERBOSE_FLAG := $(if $(VERBOSE),-v,)

# Helper function to run SQL files using Python script
# Parameters: $(1) = SQL file name (without .sql), $(2) = optional --dbrmlib argument
define run_db2cmd
	@echo "Running $(1)..."
	$(DB2_RUN) $(DB2SQL_DIR)/$(1).sql --config $(BUILD_CONFIG) $(VERBOSE_FLAG)
endef

# Helper function for DB2 grant operations
# Parameters: $(1) = SQL file name (without .sql)
# Note: Grant operations use DSNTIAD plan instead of DSNTEP2
define run_db2grant
	@echo "Running grant: $(1)..."
	@$(DB2_RUN) $(DB2GRANT_DIR)/$(1).sql --config $(BUILD_CONFIG) --use-dsntiad $(VERBOSE_FLAG)
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
	@echo "Configuration:"
	@echo "  Configuration file: $(BUILD_CONFIG)"
	@echo "  Use 'make db2-show-config' to view current settings"
	@echo ""

# Create all DB2 artifacts using INSTDB2.jcl
db2-create: db2-create-database db2-create-stogroups db2-create-tablespaces \
            db2-create-tables db2-create-indexes
	@echo "All DB2 artifacts created successfully"

# Create database
db2-create-database:
	@echo "Creating CBSA database..."
	@$(call run_db2cmd,CREDB00)
	@echo "Database created"

# Create storage groups
db2-create-stogroups:
	@echo "Creating storage groups..."
	@$(call run_db2cmd,CRESG01)
	@$(call run_db2cmd,CRESG02)
	@$(call run_db2cmd,CRESG03)
	@echo "Storage groups created"

# Create tablespaces
db2-create-tablespaces:
	@echo "Creating tablespaces..."
	@$(call run_db2cmd,CRETS01)
	@$(call run_db2cmd,CRETS02)
	@$(call run_db2cmd,CRETS03)
	@echo "Tablespaces created"

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
	@echo "Indexes created"

# Bind all packages and plan
db2-bind-all: db2-bind-packages db2-bind-plan db2-grant
	@echo "DB2 binding complete"

# Bind DB2 packages and plan
db2-bind-packages:
	@echo "Binding DB2 packages and plan..."
	$(call run_db2cmd,BIND01)
	@echo "✓ DB2 packages and plan bound successfully"
	@echo "Granting permissions to $(BANK_USER)..."
	$(call run_db2grant,grant)
	@echo "✓ Permissions granted successfully"

# Bind DB2 plan (requires packages to exist)
db2-bind-plan:
	@echo "Note: db2-bind-plan is now included in db2-bind-packages"
	@echo "Use 'make db2-bind-packages' to bind packages and plan together"

# Grant permissions
db2-grant:
	@echo "Granting permissions to $(BANK_USER)..."
	@$(call run_db2grant,grant)
	@echo "✓ Permissions granted successfully"

# Drop all DB2 artifacts
db2-drop:
	@echo "Dropping all DB2 artifacts..."
	@$(call substitute_jcl,$(DB2JCL_DIR)/DROPDB2.jcl) | $(SUBMIT_JCL)
	@echo "✓ Drop job submitted"
	@echo "Warning: This will delete all CBSA database objects"

# Test DB2 connection
db2-test:
	@echo "Testing DB2 connection..."
	@$(call substitute_jcl,$(DB2JCL_DIR)/BTCHSQL.jcl) | $(SUBMIT_JCL)
	@echo "Test query job submitted"

# Alternative: Create everything using single INSTDB2.jcl
db2-install-single:
	@echo "Creating all DB2 artifacts using INSTDB2.jcl..."
	@$(call substitute_jcl,$(DB2JCL_DIR)/INSTDB2.jcl) | $(SUBMIT_JCL)
	@echo "Installation job submitted"
	@echo "Note: This creates database, storage groups, tablespaces, tables, and indexes"

# Show current DB2 configuration
db2-show-config:
	@echo "Current DB2 Configuration:"
	@echo "=========================="
	@echo "Configuration is loaded from: $(BUILD_CONFIG)"
	@echo ""
	@echo "To view all configuration values, run:"
	@echo "  cat $(BUILD_CONFIG)"
	@echo ""

# Rebuild DB2 (drop and recreate)
db2-rebuild: db2-drop db2-create db2-bind-all
	@echo "DB2 rebuild complete"

# Made with Bob
