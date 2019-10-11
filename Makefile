.PHONY: help clean dev package test

help:
	@echo "There should be an active virtual environment before executing this file"
	@echo "Options available:"
	@echo "	 dev 	 install all dependencies"
	@echo "  clean	 removes all packages built"
	@echo "	 test	 run all tests with coverage"
	@echo "  package build distributable packages"

clean:
	rm -rf dist/*

dev:
	pip install -r dev-requirements.txt
	pip install -e .

docs:
	$(MAKE) -C docs html

package:
	python setup.py sdist
	python setup.py bdist_wheel

test:
	coverage run -m unittest discover
coverage html