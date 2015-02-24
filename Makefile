PKGNAME = cashe
PYTHON=python
NOSETESTS=nosetests-2.6
NOSETESTS=nosetests

PYFILES = __init__.py

PYVER := $(shell $(PYTHON) -c 'import sys; print "%.3s" %(sys.version)')
PYSYSDIR := $(shell $(PYTHON) -c 'import sys; print sys.prefix')
PYLIBDIR = $(PYSYSDIR)/lib/python$(PYVER)
PKGDIR = $(PYLIBDIR)/site-packages/$(PKGNAME)

all:
	@echo Done

install:
	mkdir -p $(DESTDIR)/$(PKGDIR)
	for p in $(PYFILES) ; do \
		install -m 644 $$p $(DESTDIR)/$(PKGDIR)/$$p; \
	done
	$(PYTHON) -c "import compileall; compileall.compile_dir('$(DESTDIR)/$(PKGDIR)', 1, '$(PKGDIR)', 1)"
	install -m 755 cashe-bin.py $(DESTDIR)/usr/bin/cashe

clean:
	rm -f *.pyc *.pyo *~

check test:
	@$(NOSETESTS) test.py
