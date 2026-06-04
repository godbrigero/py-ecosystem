ROOT_DIR ?= $(shell pwd)
INSTALLATION_PATHS ?=
ECOSYSTEM_DIR := $(ROOT_DIR)/ecosystem

RSYNC_FLAGS := -av --delete
RSYNC_EXCLUDES := \
	--exclude='.git/' \
	--exclude='__pycache__/' \
	--exclude='*.pyc' \
	--exclude='.DS_Store' \
	--exclude='.venv/' \
	--exclude='.env'

.PHONY: install-tools lint-imports

lint-imports:
	PYTHONPATH="$(ROOT_DIR)" lint-imports

install-tools:
ifeq ($(strip $(INSTALLATION_PATHS)),)
	$(error Set INSTALLATION_PATHS, e.g. make install-tools INSTALLATION_PATHS="/path/to/util /other/project")
endif
	@test -d "$(ECOSYSTEM_DIR)" || (echo "Missing $(ECOSYSTEM_DIR)" && exit 1)
	for path in $(INSTALLATION_PATHS); do \
		echo "Syncing ecosystem -> $$path/ecosystem/"; \
		mkdir -p "$$path/ecosystem"; \
		rsync $(RSYNC_FLAGS) $(RSYNC_EXCLUDES) "$(ECOSYSTEM_DIR)/" "$$path/ecosystem/"; \
	done
