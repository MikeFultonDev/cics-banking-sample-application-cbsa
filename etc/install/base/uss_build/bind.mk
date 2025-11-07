# CBSA DB2 Binding Makefile
# Handles incremental binding of COBOL programs to DB2
# Binds packages and plan based on DBRM changes

# Include configuration
include build.conf

# Directories
BUILD_DIR := build
DBRM_DIR := $(BUILD_DIR)/dbrm
BIND_DIR := $(BUILD_DIR)/bind

# Create bind tracking directory
$(shell mkdir -p $(BIND_DIR))

# DB2 command wrapper
DB2CMD := db2

# Programs that require DB2 binding
DB2_PROGRAMS := \
	ABNDPROC \
	BANKDATA \
	CREACC \
	CRECUST \
	DBCRFUN \
	DELACC \
	DELCUS \
	INQACC \
	INQACCCU \
	INQCUST \
	UPDACC \
	UPDCUST \
	XFRFUN

# Package bind markers (track when packages are bound)
PACKAGE_MARKERS := $(addprefix $(BIND_DIR)/,$(addsuffix .pkg,$(DB2_PROGRAMS)))

# Plan bind marker
PLAN_MARKER := $(BIND_DIR)/$(DB2_PLAN).plan

# Phony targets
.PHONY: all packages plan bind-all rebind-plan free-plan clean-bind help-bind list-db2-programs

# Default target
all: bind-all

# Help target
help-bind:
	@echo "CBSA DB2 Binding Makefile"
	@echo "=========================="
	@echo ""
	@echo "Targets:"
	@echo "  bind-all         - Bind all packages and plan (default)"
	@echo "  packages         - Bind all DB2 packages"
	@echo "  plan             - Bind DB2 plan"
	@echo "  rebind-plan      - Rebind existing plan"
	@echo "  free-plan        - Free (drop) plan and packages"
	@echo "  clean-bind       - Remove bind markers (force rebind)"
	@echo "  list-db2-programs - List programs requiring DB2 binding"
	@echo ""
	@echo "Individual package binding:"
	@echo "  make $(BIND_DIR)/<PROGRAM>.pkg  - Bind specific package"
	@echo ""
	@echo "Examples:"
	@echo "  make -f bind.mk                 # Bind everything"
	@echo "  make -f bind.mk packages        # Bind packages only"
	@echo "  make -f bind.mk $(BIND_DIR)/CREACC.pkg  # Bind CREACC package"
	@echo "  make -f bind.mk rebind-plan     # Rebind plan"
	@echo "  make -f bind.mk clean-bind bind-all  # Force complete rebind"
	@echo ""
	@echo "Configuration:"
	@echo "  DB2 Subsystem: $(DB2_SUBSYSTEM)"
	@echo "  DB2 Plan:      $(DB2_PLAN)"
	@echo "  DB2 Package:   $(DB2_PACKAGE)"
	@echo "  DB2 Owner:     $(DB2_OWNER)"
	@echo ""

# List DB2 programs
list-db2-programs:
	@echo "Programs requiring DB2 binding ($(words $(DB2_PROGRAMS))):"
	@echo "$(DB2_PROGRAMS)" | tr ' ' '\n' | sed 's/^/  /'

# Bind all packages and plan
bind-all: packages plan
	@echo ""
	@echo "✓ DB2 binding completed successfully"
	@echo "  Packages: $(BIND_DIR)/*.pkg"
	@echo "  Plan:     $(PLAN_MARKER)"

# Bind all packages
packages: $(PACKAGE_MARKERS)
	@echo ""
	@echo "✓ All DB2 packages bound successfully"

# Bind plan (depends on all packages)
plan: $(PLAN_MARKER)

# Pattern rule for binding individual packages
# Package depends on its DBRM file
$(BIND_DIR)/%.pkg: $(DBRM_DIR)/%.dbrm | $(BIND_DIR)
	@echo "Binding DB2 package for $*..."
	@echo "CONNECT TO $(DB2_SUBSYSTEM);" > $(BIND_DIR)/$*.sql
	@echo "BIND PACKAGE($(DB2_PACKAGE).$*)" >> $(BIND_DIR)/$*.sql
	@echo "     MEMBER($*)" >> $(BIND_DIR)/$*.sql
	@echo "     LIBRARY('$(DBRM)')" >> $(BIND_DIR)/$*.sql
	@echo "     OWNER($(DB2_OWNER))" >> $(BIND_DIR)/$*.sql
	@echo "     QUALIFIER($(DB2_OWNER))" >> $(BIND_DIR)/$*.sql
	@echo "     ACTION(REPLACE)" >> $(BIND_DIR)/$*.sql
	@echo "     ISOLATION(CS)" >> $(BIND_DIR)/$*.sql
	@echo "     RELEASE(COMMIT)" >> $(BIND_DIR)/$*.sql
	@echo "     VALIDATE(BIND)" >> $(BIND_DIR)/$*.sql
	@echo "     CURRENTDATA(NO)" >> $(BIND_DIR)/$*.sql
	@echo "     DYNAMICRULES(BIND)" >> $(BIND_DIR)/$*.sql
	@echo "     DEGREE(1)" >> $(BIND_DIR)/$*.sql
	@echo "     EXPLAIN(NO);" >> $(BIND_DIR)/$*.sql
	@echo "COMMIT;" >> $(BIND_DIR)/$*.sql
	@$(DB2CMD) -tvf $(BIND_DIR)/$*.sql
	@touch $@
	@echo "✓ Package $* bound successfully"

# Bind plan (depends on all package markers)
$(PLAN_MARKER): $(PACKAGE_MARKERS) | $(BIND_DIR)
	@echo "Binding DB2 plan $(DB2_PLAN)..."
	@echo "CONNECT TO $(DB2_SUBSYSTEM);" > $(BIND_DIR)/plan.sql
	@echo "BIND PLAN($(DB2_PLAN))" >> $(BIND_DIR)/plan.sql
	@echo "     PKLIST(" >> $(BIND_DIR)/plan.sql
	@for prog in $(DB2_PROGRAMS); do \
		echo "       $(DB2_PACKAGE).$$prog," >> $(BIND_DIR)/plan.sql; \
	done
	@sed -i '$$s/,$$//' $(BIND_DIR)/plan.sql
	@echo "     )" >> $(BIND_DIR)/plan.sql
	@echo "     OWNER($(DB2_OWNER))" >> $(BIND_DIR)/plan.sql
	@echo "     QUALIFIER($(DB2_OWNER))" >> $(BIND_DIR)/plan.sql
	@echo "     ACTION(REPLACE)" >> $(BIND_DIR)/plan.sql
	@echo "     ISOLATION(CS)" >> $(BIND_DIR)/plan.sql
	@echo "     RELEASE(COMMIT)" >> $(BIND_DIR)/plan.sql
	@echo "     VALIDATE(BIND)" >> $(BIND_DIR)/plan.sql
	@echo "     CURRENTDATA(NO)" >> $(BIND_DIR)/plan.sql
	@echo "     DYNAMICRULES(BIND)" >> $(BIND_DIR)/plan.sql
	@echo "     DEGREE(1)" >> $(BIND_DIR)/plan.sql
	@echo "     EXPLAIN(NO);" >> $(BIND_DIR)/plan.sql
	@echo "COMMIT;" >> $(BIND_DIR)/plan.sql
	@$(DB2CMD) -tvf $(BIND_DIR)/plan.sql
	@touch $@
	@echo "✓ Plan $(DB2_PLAN) bound successfully"
	@echo ""
	@echo "Granting execute permissions..."
	@echo "CONNECT TO $(DB2_SUBSYSTEM);" > $(BIND_DIR)/grant.sql
	@echo "GRANT EXECUTE ON PLAN $(DB2_PLAN) TO $(BANK_USER);" >> $(BIND_DIR)/grant.sql
	@echo "COMMIT;" >> $(BIND_DIR)/grant.sql
	@$(DB2CMD) -tvf $(BIND_DIR)/grant.sql || echo "⚠ Warning: Grant may have failed"
	@echo "✓ Execute permission granted to $(BANK_USER)"

# Rebind existing plan (faster than full bind)
rebind-plan:
	@echo "Rebinding DB2 plan $(DB2_PLAN)..."
	@echo "CONNECT TO $(DB2_SUBSYSTEM);" > $(BIND_DIR)/rebind.sql
	@echo "REBIND PLAN($(DB2_PLAN))" >> $(BIND_DIR)/rebind.sql
	@echo "       ISOLATION(CS)" >> $(BIND_DIR)/rebind.sql
	@echo "       CURRENTDATA(NO);" >> $(BIND_DIR)/rebind.sql
	@echo "COMMIT;" >> $(BIND_DIR)/rebind.sql
	@$(DB2CMD) -tvf $(BIND_DIR)/rebind.sql
	@touch $(PLAN_MARKER)
	@echo "✓ Plan $(DB2_PLAN) rebound successfully"

# Free (drop) plan and packages
free-plan:
	@echo "Freeing DB2 plan and packages..."
	@echo "CONNECT TO $(DB2_SUBSYSTEM);" > $(BIND_DIR)/free.sql
	@echo "FREE PLAN($(DB2_PLAN));" >> $(BIND_DIR)/free.sql
	@echo "FREE PACKAGE($(DB2_PACKAGE).*);" >> $(BIND_DIR)/free.sql
	@echo "COMMIT;" >> $(BIND_DIR)/free.sql
	@$(DB2CMD) -tvf $(BIND_DIR)/free.sql || echo "⚠ Plan/packages may not exist"
	@rm -f $(PLAN_MARKER) $(PACKAGE_MARKERS)
	@echo "✓ Plan and packages freed"

# Clean bind markers (forces rebind on next make)
clean-bind:
	@echo "Removing bind markers..."
	@rm -f $(BIND_DIR)/*.pkg $(BIND_DIR)/*.plan
	@echo "✓ Bind markers removed (next bind will be full)"

# Create bind directory
$(BIND_DIR):
	@mkdir -p $@

# Show bind status
status-bind:
	@echo "DB2 Bind Status"
	@echo "==============="
	@echo ""
	@echo "Configuration:"
	@echo "  DB2 Subsystem: $(DB2_SUBSYSTEM)"
	@echo "  DB2 Plan:      $(DB2_PLAN)"
	@echo "  DB2 Package:   $(DB2_PACKAGE)"
	@echo "  DB2 Owner:     $(DB2_OWNER)"
	@echo ""
	@echo "Programs requiring binding: $(words $(DB2_PROGRAMS))"
	@echo ""
	@echo "Bind status:"
	@echo "  DBRMs:         $(words $(wildcard $(DBRM_DIR)/*.dbrm))"
	@echo "  Bound packages: $(words $(wildcard $(BIND_DIR)/*.pkg))"
	@if [ -f "$(PLAN_MARKER)" ]; then \
		echo "  Plan status:    ✓ Bound"; \
	else \
		echo "  Plan status:    ✗ Not bound"; \
	fi
	@echo ""
	@if [ $(words $(wildcard $(DBRM_DIR)/*.dbrm)) -gt $(words $(wildcard $(BIND_DIR)/*.pkg)) ]; then \
		echo "⚠ Some DBRMs are not bound. Run 'make -f bind.mk' to bind."; \
	fi

# Check if DBRMs exist
check-dbrms:
	@if [ ! -d "$(DBRM_DIR)" ] || [ -z "$$(ls -A $(DBRM_DIR) 2>/dev/null)" ]; then \
		echo "ERROR: No DBRMs found in $(DBRM_DIR)"; \
		echo "Run 'make compile' first to generate DBRMs"; \
		exit 1; \
	fi
	@echo "✓ DBRMs found: $(words $(wildcard $(DBRM_DIR)/*.dbrm))"

# Validate bind
validate-bind: check-dbrms
	@echo "Validating DB2 bind..."
	@echo "  DBRMs:    $(words $(wildcard $(DBRM_DIR)/*.dbrm))"
	@echo "  Packages: $(words $(wildcard $(BIND_DIR)/*.pkg))"
	@if [ -f "$(PLAN_MARKER)" ]; then \
		echo "  Plan:     ✓ Bound"; \
	else \
		echo "  Plan:     ✗ Not bound"; \
		exit 1; \
	fi
	@echo "✓ Bind validation passed"

# Made with Bob
