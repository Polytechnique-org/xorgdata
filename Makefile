PACKAGE     = xorgdata
SRC_DIR     = $(PACKAGE)
TESTS_DIR   = tests

# Utilise le binaire Python courant
COVERAGE    = python -m coverage
RUFF        = ruff
DJANGO_ADMIN = django-admin

PO_FILES = $(shell find $(SRC_DIR) -name '*.po')
MO_FILES = $(PO_FILES:.po=.mo)

all: default

default: build

clean:
	find . -type f -name '*.pyc' -delete
	find $(SRC_DIR) $(TESTS_DIR) -type f -path '*/__pycache__/*' -delete
	find . -type d -empty -delete
	rm -f $(MO_FILES)
	@rm -rf tmp_test/

build: $(MO_FILES)

createdb:
	mkdir -p dev
	python manage.py migrate

%.mo: %.po
	cd $(abspath $(dir $<)/../../..) && $(DJANGO_ADMIN) compilemessages

poupdate:
	python manage.py makemessages --locale=fr --ignore=.tox

update:
	pip install --upgrade pip setuptools
	pip install --upgrade -r requirements_dev.txt
	pip freeze

testall:
	tox

test: build
	PYTHONPATH=.:$$PYTHONPATH python -Wdefault manage.py test $(TESTS_DIR)

checkdeploy:
	python manage.py check --deploy --fail-level WARNING

lint:
	check-manifest
	$(RUFF) check $(SRC_DIR) $(TESTS_DIR)

format:
	$(RUFF) format $(SRC_DIR) $(TESTS_DIR)

coverage:
	$(COVERAGE) erase
	$(COVERAGE) run --branch manage.py test $(TESTS_DIR)
	$(COVERAGE) report
	$(COVERAGE) html

.PHONY: all checkdeploy clean coverage createdb default doc format lint poupdate test testall update
