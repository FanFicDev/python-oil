requirements_in := $(wildcard requirements/*.in)
requirements := $(patsubst %.in,%.txt,$(requirements_in))

default: lint build

lint: venv/
	./venv/bin/mypy src/
	./venv/bin/ruff format src/
	./venv/bin/ruff check src/

build: venv/ requires setup.cfg lint
	./venv/bin/python -m build

venv/:
	python3 -m venv ./venv
	./venv/bin/python -m pip install --upgrade pip pip-tools
	make requirements/dev.txt
	./venv/bin/python -m pip install -r requirements/dev.txt

setup.cfg: requirements/install_simple.txt setup.head.cfg setup.tail.cfg
	cat setup.head.cfg  > $@
	sed 's/^/\t/' $<   >> $@
	cat setup.tail.cfg >> $@

requires: $(requirements) requirements/install_simple.txt

requirements/%_simple.txt: requirements/%.in venv/
	./venv/bin/pip-compile --strip-extras --no-header --no-annotate $< -o $@

requirements/%.txt: requirements/%.in $(requirements_in) venv/
	./venv/bin/pip-compile --strip-extras --no-header $<

clean:
	rm -f requirements/*.txt

spotless: clean
	rm -fr venv/ dist/ src/*.egg-info/

.PHONY: requires clean spotless build lint

