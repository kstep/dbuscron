
DESTDIR ?= 
PYMODULES ?= $(DESTDIR)/usr/lib/pymodules/python2.5
PREFIX ?= $(DESTDIR)/usr/bin
PYSUFFIX = `test -e ./dbuscron/__init__.pyo && echo pyo || echo pyc`
PYVERSION ?= 2.5

all:
	@echo "No compilation needed."

install:
	install -o root -g root -m 0755 ./dbuscron.py $(PREFIX)/dbuscron
	install -o root -g root -m 0755 ./dbuscrontab.py $(PREFIX)/dbuscrontab
	install -o root -g root -m 0755 -d $(PYMODULES)/dbuscron/shell
	python$(PYVERSION) -O -c 'import dbuscron, dbuscron.shell.main, dbuscron.shell.edit'
	install -o root -g root -m 0644 ./dbuscron/*.$(PYSUFFIX) $(PYMODULES)/dbuscron
	install -o root -g root -m 0644 ./dbuscron/shell/*.$(PYSUFFIX) $(PYMODULES)/dbuscron/shell
	install -o root -g root -m 0644 ./event.d/dbuscron $(DESTDIR)/etc/event.d/dbuscron
	-test ! -f $(DESTDIR)/etc/dbuscrontab && \
		install -o root -g root -m 0644 ./doc/dbuscrontab $(DESTDIR)/etc/dbuscrontab
	@echo "Installation complete. Run \`dbuscrontab -e' to edit config file,"
	@echo "then run \`initctl start dbuscron' to start dbuscron daemon."

uninstall:
	-initctl stop dbuscron
	rm -rf $(PYMODULES)/dbuscron
	rm -f $(PREFIX)/dbuscron $(PREFIX)/dbuscrontab
	rm -f $(DESTDIR)/etc/event.d/dbuscron

clean:
	find ./dbuscron -name "*.py[co]" | xargs rm -f 

debclean:
	debclean
	rm -rf ./debian/patches ./debian/dbuscron
	rm -rf ./.pc

deb: debclean
	debuild binary-indep

.PHONY: all install uninstall clean debclean deb

