# CBSA DB2 Management Makefile
# Manages DB2 database, tables, indexes, packages, and plans using batchtsocmd 0.2.1 CLI
# Copyright IBM Corp. 2023, 2025

.PHONY: db2-help db2-create db2-drop db2-bind-packages db2-bind-plan db2-bind-all \
        db2-create-database db2-create-stogroups db2-create-tablespaces \
        db2-create-tables db2-create-indexes db2-grant db2-rebuild db2-show-config

# DB2 SQL and grant directories
DB2SQL_DIR := $(mkfile_dir)/db2sql
DB2GRANT_DIR := $(mkfile_dir)/db2grant

# build.conf path and envsubst utility (db2subst is a backward-compatible wrapper)
# Use = (deferred) so $(PYTHON) expands at use time (PYTHON is defined in parent Makefile)
BUILD_CONF = $(mkfile_dir)/build.conf
ENVSUBST   = $(PYTHON) $(mkfile_dir)/bin/envsubst
DB2SUBST   = $(ENVSUBST)

# Verbose flag
VERBOSE_FLAG := $(if $(VERBOSE),-v,)

# Helper function to run SQL files via db2sql CLI
# db2subst expands ${VAR} from build.conf, pipes result to db2sql via stdin
# Parameters: $(1) = SQL file name (without .sql)
define run_db2cmd
	@echo "Running $(1)..."
	. $(BUILD_CONF) && $(DB2SUBST) $(DB2SQL_DIR)/$(1).sql --config $(BUILD_CONF) | \
	    db2sql \
	    --system $${DB2_SYSTEM} \
	    --plan $${DB2_DSNTEP_PLAN} \
	    --toollib $${DB2_TOOLLIB} \
	    --steplib $${DB2_HLQ}.SDSNEXIT:$${DB2_HLQ}.SDSNLOAD \
	    $(VERBOSE_FLAG)
endef

# Helper function for DB2 grant operations via db2sql CLI
# Parameters: $(1) = SQL file name (without .sql)
# Note: GRANT is plain SQL executed via DSNTEP2 (db2sql), not DSNTIAD
define run_db2grant
	@echo "Running grant: $(1)..."
	. $(BUILD_CONF) && $(DB2SUBST) $(DB2GRANT_DIR)/$(1).sql --config $(BUILD_CONF) | \
	    db2sql \
	    --system $${DB2_SYSTEM} \
	    --plan $${DB2_DSNTEP_PLAN} \
	    --toollib $${DB2_TOOLLIB} \
	    --steplib $${DB2_HLQ}.SDSNEXIT:$${DB2_HLQ}.SDSNLOAD \
	    $(VERBOSE_FLAG)
endef

# DB2 Help
db2-help:
	@echo "CBSA DB2 Management Targets"
	@echo "============================"
	@echo ""
	@echo "Database Creation:"
	@echo "  db2-create             - Create all DB2 artifacts (database, tables, indexes)"
	@echo "  db2-create-database    - Create CBSA database only"
	@echo "  db2-create-stogroups   - Create storage groups only"
	@echo "  db2-create-tablespaces - Create tablespaces only"
	@echo "  db2-create-tables      - Create tables only"
	@echo "  db2-create-indexes     - Create indexes only"
	@echo ""
	@echo "DB2 Binding:"
	@echo "  db2-bind-all           - Bind packages and grant permissions"
	@echo "  db2-bind-packages      - Bind DB2 packages and plan"
	@echo "  db2-grant              - Grant permissions"
	@echo ""
	@echo "Database Cleanup:"
	@echo "  db2-drop               - Drop all DB2 artifacts"
	@echo "  db2-rebuild            - Drop and recreate all DB2 artifacts"
	@echo ""
	@echo "Configuration:"
	@echo "  db2-show-config        - Show current DB2 configuration"
	@echo ""
	@echo "Configuration file: $(BUILD_CONF)"
	@echo ""
	@echo "Note: db2-bind-packages now binds both packages and plan together."
	@echo "      The separate db2-bind-plan target has been deprecated."
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
db2-bind-all: db2-bind-packages db2-grant
	@echo "DB2 binding complete"

# Bind DB2 packages and plan using db2bind CLI
# db2bind generates SYSTSIN directly - no SQL substitution needed
db2-bind-packages:
	@echo "Binding DB2 packages and plan..."
	. $(BUILD_CONF) && db2bind \
	    --system $${DB2_SYSTEM} \
	    --package $${CBSA_PACKAGE} \
	    --owner $${DB2_OWNER} \
	    --qualifier $${DB2_OWNER} \
	    --action REPLACE \
	    --member CREACC \
	    --member CRECUST \
	    --member DBCRFUN \
	    --member DELACC \
	    --member DELCUS \
	    --member INQACC \
	    --member INQACCCU \
	    --member BANKDATA \
	    --member UPDACC \
	    --member XFRFUN \
	    --plan $${CBSA_PLAN} \
	    --isolation UR \
	    --pklist "NULLID.*" \
	    --pklist "$${CBSA_PACKAGE}.*" \
	    --library $(OBJ_DIR) \
	    --steplib $${DB2_HLQ}.SDSNEXIT:$${DB2_HLQ}.SDSNLOAD \
	    $(VERBOSE_FLAG)
	@echo "✓ DB2 packages and plan bound successfully"

# Bind DB2 plan (requires packages to exist)
db2-bind-plan:
	@echo "Note: db2-bind-plan is now included in db2-bind-packages"
	@echo "Use 'make db2-bind-packages' to bind packages and plan together"

# Grant permissions via db2sql CLI (GRANT is plain SQL via DSNTEP2)
db2-grant:
	@echo "Granting permissions..."
	@$(call run_db2grant,grant)
	@echo "✓ Permissions granted successfully"

# Drop all DB2 artifacts
db2-drop:
	@echo "Dropping all DB2 artifacts..."
	@$(call run_db2cmd,drop-db2)
	@echo "✓ DB2 artifacts dropped successfully"

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
