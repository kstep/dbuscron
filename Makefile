
DESTDIR ?= 
PYMODULES ?= $(DESTDIR)/usr/lib/pymodules/python2.5
PREFIX ?= $(DESTDIR)/usr/bin
PYVERSION ?= 2.5

BINFILES = dbuscron.py dbuscrontab.py migrate-dbus-scripts.py

.SUFFIXES: .py .pyo

compile: .py.pyo

.py.pyo:
	python$(PYVERSION) -O -m compileall ./dbuscron

install: compile
	for f in $(BINFILES); do \
		install -o root -g root -m 0755 ./$$f $(PREFIX)/`basename $$f .py`; done
	install -o root -g root -m 0755 -d $(PYMODULES)/dbuscron/shell
	for f in `find ./dbuscron -name "*.pyo"`; do \
		install -o root -g root -m 0644 $$f $(PYMODULES)/$$f; done
	install -o root -g root -m 0644 ./event.d/dbuscron $(DESTDIR)/etc/event.d/dbuscron
	test -f $(DESTDIR)/etc/dbuscrontab || \
		install -o root -g root -m 0644 ./doc/dbuscrontab $(DESTDIR)/etc/dbuscrontab
	@echo ""
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

build: debclean
	./genchangelog $(B)
	git commit -m "changelog updated" ./debian/changelog
	git tag -f v$(B)
	$(MAKE) deb

tarball:
	git archive --format=tar v$(B) | gzip -9 > ../dbuscron_$(B:.0=).orig.tar.gz

debuild: tarball
	debuild -aarmel

publish: debuild
	scp ../dbuscron_$(B:.0=)*.tar.gz drop.maemo.org:/var/www/extras-devel/incoming-builder/fremantle
	scp ../dbuscron_$(B:.0=)*.changes drop.maemo.org:/var/www/extras-devel/incoming-builder/fremantle
	scp ../dbuscron_$(B:.0=)*.dsc drop.maemo.org:/var/www/extras-devel/incoming-builder/fremantle

.PHONY: install uninstall clean debclean deb build compile tarball debuild publish

