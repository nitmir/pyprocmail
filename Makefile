.PHONY: clean build install dist uninstall
VERSION=`python setup.py -V`

build:
	python setup.py build

install: dist
	pip install pyprocmail -U -f ./dist/pyprocmail-${VERSION}.tar.gz
uninstall:
	pip uninstall pyprocmail || true
reinstall: uninstall install

clean_pyc:
	find ./ -name '*.pyc' -delete
	find ./ -name __pycache__ -delete
clean_build:
	rm -rf build policyd_rate_limit.egg-info dist
clean: clean_pyc clean_build
	find ./ -name '*~' -delete

dist:
	python setup.py sdist
