# -*- coding: utf-8 -*-

# Resource object code
#
# Created: Fr 1. Mrz 10:54:06 2013
#      by: The Resource Compiler for PySide (Qt v4.8.4)
#
# WARNING! All changes made in this file will be lost!

from PySide import QtCore

qt_resource_name = "\x00\x0d\x05g=\x1f\x00P\x00i\x00e\x00-\x00c\x00h\x00a\x00r\x00t\x00.\x00i\x00c\x00o"
qt_resource_struct = "\x00\x00\x00\x00\x00\x02\x00\x00\x00\x01\x00\x00\x00\x01\x00\x00\x00\x00\x00\x00\x00\x00\x00\x01\x00\x00\x00\x00"
def qInitResources():
    QtCore.qRegisterResourceData(0x01, qt_resource_struct, qt_resource_name, qt_resource_data)

def qCleanupResources():
    QtCore.qUnregisterResourceData(0x01, qt_resource_struct, qt_resource_name, qt_resource_data)

qInitResources()