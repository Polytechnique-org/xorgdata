PACKAGE=xorgdata
SRC_DIR=$(PACKAGE)
TESTS_DIR=tests
DOC_DIR=docs

# Use current python binary instead of system default.
COVERAGE = python $(shell which coverage)
FLAKE8 = flake8
DJANGO_ADMIN = django-admin.py
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
	python manage.py creatersakey

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
	$(FLAKE8) --config .flake8 $(SRC_DIR)
	$(FLAKE8) --config .flake8 $(TESTS_DIR)

coverage:
	$(COVERAGE) erase
	$(COVERAGE) run "--include=$(SRC_DIR)/*.py,$(TESTS_DIR)/*.py" --branch manage.py test $(TESTS_DIR)
	$(COVERAGE) report "--include=$(SRC_DIR)/*.py,$(TESTS_DIR)/*.py"
	$(COVERAGE) html "--include=$(SRC_DIR)/*.py,$(TESTS_DIR)/*.py"

doc:
	$(MAKE) -C $(DOC_DIR) html


.PHONY: all checkdeploy clean coverage createdb default doc install-deps lint poupdate test testall update
