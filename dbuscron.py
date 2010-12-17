#!/usr/bin/python
#
# bus type sender interface path member destination args command
#
# Examples for N900:
#
# Headphones unplugged:
# S signal * org.freedesktop.Hal.Device /org/freedesktop/Hal/devices/platform_headphone Condition * ButtonPressed;connection echo Headphones state changed: $(cat /sys/devices/platform/gpio-switch/headphone/state)
#
# Call recieved:
# S signal * com.nokia.csd.Call /com/nokia/csd/call Coming * * echo $DBUS_ARG1 is calling
#

from dbuscron.shell import main
main.run()

# vim: ts=8 sts=4 sw=4 et

