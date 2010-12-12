
PYMODULES ?= /usr/lib/pymodules/python2.5
PREFIX ?= /usr/bin
PYSUFFIX = `test -e ./dbuscron/__init__.pyo && echo pyo || echo pyc`

install:
	install -o root -g root -m 0755 ./dbuscron.py $(PREFIX)/dbuscron
	install -o root -g root -m 0755 ./dbuscrontab.py $(PREFIX)/dbuscrontab
	install -o root -g root -m 0755 -d $(PYMODULES)/dbuscron
	python -c 'import dbuscron'
	install -o root -g root -m 0644 ./dbuscron/*.$(PYSUFFIX) $(PYMODULES)/dbuscron
	install -o root -g root -m 0644 ./event.d/dbuscron /etc/event.d/dbuscron
	touch /etc/dbuscrontab
	@echo "Installation complete. Run \`dbuscrontab -e' to edit config file,"
	@echo "then run \`initctl start dbuscron' to start dbuscron daemon."

uninstall:
	-initctl stop dbuscron
	rm -rf $(PYMODULES)/dbuscron
	rm -f $(PREFIX)/dbuscron $(PREFIX)/dbuscrontab
	rm -f /etc/event.d/dbuscron

clean:
	find . -name "*.py[co]" | xargs rm -f 

