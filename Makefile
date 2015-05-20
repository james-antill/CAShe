PKGNAME = cashe
VERSION=0.99.2
RELEASE=1
PYTHON=python
NOSETESTS=nosetests-2.6
NOSETESTS=nosetests

PYFILES = __init__.py

PYVER := $(shell $(PYTHON) -c 'import sys; print "%.3s" %(sys.version)')
PYSYSDIR := $(shell $(PYTHON) -c 'import sys; print sys.prefix')
PYLIBDIR = $(PYSYSDIR)/lib/python$(PYVER)
PKGDIR = $(PYLIBDIR)/site-packages/$(PKGNAME)

XSLTPROC = xsltproc
XSLTPROC_FLAGS = \
        --nonet \
        --stringparam man.output.quietly 1 \
        --stringparam funcsynopsis.style ansi \
        --stringparam man.th.extra1.suppress 1 \
        --stringparam man.authors.section.enabled 0 \
        --stringparam man.copyright.section.enabled 0

XSLTPROC_FLAGS_MAN = \
        $(XSLTPROC_FLAGS) http://docbook.sourceforge.net/release/xsl/current/manpages/docbook.xsl

all: cashe.1
	@echo Done

install-py:
	mkdir -p $(DESTDIR)/$(PKGDIR)
	for p in $(PYFILES) ; do \
		install -m 644 $$p $(DESTDIR)/$(PKGDIR)/$$p; \
	done
	$(PYTHON) -c "import compileall; compileall.compile_dir('$(DESTDIR)/$(PKGDIR)', 1, '$(PKGDIR)', 1)"

install-bin:
	mkdir -p $(DESTDIR)/usr/bin
	install -m 755 cashe-bin.py $(DESTDIR)/usr/bin/cashe

install-doc: cashe.1
	mkdir -p $(DESTDIR)/usr/share/man/man1
	install -m 644 cashe.1 $(DESTDIR)/usr/share/man/man1/cashe.1


install: install-py install-bin install-doc

clean:
	rm -f *.pyc *.pyo *~ cashe.1 ${PKGNAME}-%{VERSION}.tar.gz

check test:
	@$(NOSETESTS) test.py

archive: cashe.py ${PKGNAME}.spec Makefile
	@rm -rf ${PKGNAME}-%{VERSION}.tar.gz
	@rm -rf /tmp/${PKGNAME}-$(VERSION) /tmp/${PKGNAME}
	@dir=$$PWD; cd /tmp; git clone $$dir ${PKGNAME}
	@rm -rf /tmp/${PKGNAME}/.git
	@sed -i -e "s/Release: 1/Release: $(RELEASE)/" /tmp/${PKGNAME}/${PKGNAME}.spec
	@mv /tmp/${PKGNAME} /tmp/${PKGNAME}-$(VERSION)
	@dir=$$PWD; cd /tmp; tar cvzf $$dir/${PKGNAME}-$(VERSION).tar.gz ${PKGNAME}-$(VERSION)
	@rm -rf /tmp/${PKGNAME}-$(VERSION)      
	@echo "The archive is in ${PKGNAME}-$(VERSION).tar.gz"

${PKGNAME}-$(VERSION).tar.gz: archive

rpm: ${PKGNAME}-$(VERSION).tar.gz
	@rpmbuild -ts ${PKGNAME}-$(VERSION).tar.gz

cashe.1: man/cashe.xml
	$(XSLTPROC) $(XSLTPROC_FLAGS_MAN) $<
