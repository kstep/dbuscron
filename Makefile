
DESTDIR ?= 
PYMODULES ?= $(DESTDIR)/usr/lib/pymodules/python2.5
PREFIX ?= $(DESTDIR)/usr/bin
PYVERSION ?= 2.5

.SUFFIXES: .py .pyo

compile: .py.pyo

.py.pyo:
	sed -i.bak -e "s/%VERSION%/`git describe --tags`/" ./dbuscron/__init__.py
	python$(PYVERSION) -O -m compileall ./dbuscron
	mv -f ./dbuscron/__init__.py.bak ./dbuscron/__init__py

install: compile
	install -o root -g root -m 0755 ./dbuscron.py $(PREFIX)/dbuscron
	install -o root -g root -m 0755 ./dbuscrontab.py $(PREFIX)/dbuscrontab
	install -o root -g root -m 0755 -d $(PYMODULES)/dbuscron/shell
	find ./dbuscron -name "*.pyo" | xargs -I {} install -o root -g root -m 0644 {} $(PYMODULES)/{}
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
	git push -f origin v$(B)
	$(MAKE) deb

.PHONY: install uninstall clean debclean deb build compile

