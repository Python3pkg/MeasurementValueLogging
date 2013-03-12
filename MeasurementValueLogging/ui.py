# Python Measurement Value Logging Software.
# Graphical User Interface
# 
# Copyright (C) 2013  Leonard Lausen <leonard@lausen.nl>
# 
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# any later version.
# 
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
# 
# You should have received a copy of the GNU General Public License
# along with this program.  If not, see <http://www.gnu.org/licenses/>.

import sys
import pkgutil
import qr
from PyQt4 import QtCore, QtGui, uic
from devices.devicemanager import DeviceManager, DeviceConfig

class NewDeviceDialog(QtGui.QDialog):
    """Dialog to add new devices."""

    def __init__(self, dm, parent=None):
        """

        :param dm: DeviceManager
        :type dm: DeviceManager

        """

        QtGui.QDialog.__init__(self, parent)
        qfile = QtCore.QFile(":/ui/newDeviceDialog.ui")
        qfile.open(QtCore.QIODevice.ReadOnly)
        self.ui = uic.loadUi(qfile, self)
        self.dm = dm

        self.deviceComboBox.addItems(self.dm.getValidDevices())
        self.portComboBox.addItems(self.dm.getAvailiablePorts())


class DoReallyDialog(QtGui.QDialog):
    """Dialog to ask whether a user wants really to do something."""

    def __init__(self, title, text, parent=None):
        """

        :param title: Dialog title
        :type title: String
        :param text: Dialog text
        :type text: String

        """

        QtGui.QDialog.__init__(self, parent)
        qfile = QtCore.QFile(":/ui/doReallyDialog.ui")
        qfile.open(QtCore.QIODevice.ReadOnly)
        self.ui = uic.loadUi(qfile, self)

        self.windowTitle = title
        self.label.setText(text)


class Xls200Dialog(QtGui.QDialog):
    """Dialog to chose XLS200 subdevices."""

    def __init__(self, parent=None):
        QtGui.QDialog.__init__(self, parent)
        qfile = QtCore.QFile(":/ui/xls200Dialog.ui")
        qfile.open(QtCore.QIODevice.ReadOnly)
        self.ui = uic.loadUi(qfile, self)

        settings = QtCore.QSettings()


class SettingsDialog(QtGui.QDialog):
    """The general settings dialog."""

    def __init__(self, parent=None):
        QtGui.QDialog.__init__(self, parent)
        qfile = QtCore.QFile(":/ui/settingsDialog.ui")
        qfile.open(QtCore.QIODevice.ReadOnly)
        self.ui = uic.loadUi(qfile, self)

        self.pathButton.clicked.connect(self.openFile)
        self.saveButton.clicked.connect(self.save)

        self.settings = QtCore.QSettings()

        self.path.setText(self.settings.value("office/path", "").toString())
        self.loggingInterval.setValue(self.settings.value("logging/interval", 1).toInt()[0])
        self.languageComboBox.setCurrentIndex(self.settings.value("i18n", -1).toInt()[0])

    def openFile(self):
        """Open a QFileDialog and save the path."""

        import os
        popup = QtGui.QFileDialog()
        self.path.setText(popup.getOpenFileName(self, self.tr("Search Office"), os.path.expanduser("~"), ""))

    def save(self):
        """Save the settings to QSettings."""

        self.settings.setValue("office/path", self.path.text())
        self.settings.setValue("logging/interval", self.loggingInterval.value())
        self.settings.setValue("i18n", self.languageComboBox.currentIndex())


class DevicemanagerDialog(QtGui.QDialog):
    """A DeviceManager Dialog where one could delete or add new devices."""

    ids = []

    def __init__(self, dm, parent=None):
        """

        :param dm: DeviceManager
        :type dm: DeviceManager

        """

        QtGui.QDialog.__init__(self, parent)
        qfile = QtCore.QFile(":/ui/devicemanagerDialog.ui")
        qfile.open(QtCore.QIODevice.ReadOnly)
        self.ui = uic.loadUi(qfile, self)
        self.dm = dm

        self.deleteButton.clicked.connect(self.deleteItem)
        self.deleteButton.setIcon(QtGui.QIcon(":/images/close.png"))

        self.refreshList()

    def refreshList(self):
        """Refresh the list of devices."""

        self.ids = self.dm.getAllDeviceIDs()

        self.listWidget.clear()

        for id in self.ids:
            item = QtGui.QListWidgetItem(str(self.dm.getDevice(id)))
            self.listWidget.addItem(item)

    def deleteItem(self):
        """Close the device and refresh list."""

        row = self.listWidget.currentRow()

        self.dm.closeDevice(self.ids[row])
        self.dm.closeEmptyMultiboxDevices()

        self.refreshList()


class DisplayWidget(QtGui.QWidget):
    """Widget containing a lcd display and buttons to modify or delete a device."""
    calibrationType = 1 # 0: two values calibration, 1: slope and intercept calibration
    twoValueCalibration = (0.0, 0.0), (1.0, 1.0)
    slopeInterceptCalibration = 1.0, 0.0
    calibration = 1.0, 0.0 # this is either the same as slopeInterceptCalibration or twoValueCalibration
    unit = ""

    def __init__(self, deviceID, dm, parent=None):
        """

        :param deviceID: DeviceID
        :type deviceID: DeviceID
        :param dm: DeviceManager
        :type dm: DeviceManager

        """

        QtGui.QWidget.__init__(self, parent)
        qfile = QtCore.QFile(":/ui/displayWidget.ui")
        qfile.open(QtCore.QIODevice.ReadOnly)
        self.ui = uic.loadUi(qfile, self)

        self.deviceID = deviceID
        self.dm = dm
        self.deviceName.setText(str(dm.getDevice(self.deviceID)))

        self.settingsButton.clicked.connect(self.deviceSettings)
        self.deleteButton.clicked.connect(self.close)

        self.settingsButton.setIcon(QtGui.QIcon(":/images/settings.png"))
        self.deleteButton.setIcon(QtGui.QIcon(":/images/close.png"))

    def deviceSettings(self):
        """Open a DeviceSettingsDialog."""

        popup = DeviceSettingsDialog(self.deviceID, self.dm)

        popup.slope.setValue(self.slopeInterceptCalibration[0])
        popup.intercept.setValue(self.slopeInterceptCalibration[1])
        popup.is1.setValue(self.twoValueCalibration[0][0])
        popup.should1.setValue(self.twoValueCalibration[0][1])
        popup.is2.setValue(self.twoValueCalibration[1][0])
        popup.should2.setValue(self.twoValueCalibration[1][1])

        if self.calibrationType == 1:
            popup.slopeInterceptButton.setChecked(True)
        elif self.calibrationType == 0:
            popup.valuesButton.setChecked(True)

        popup.unit.setText(self.unit)

        popup.exec_()

        self.twoValueCalibration = (popup.is1.value(), popup.should1.value()), (popup.is2.value(), popup.should2.value())
        self.slopeInterceptCalibration = popup.slope.value(), popup.intercept.value()

        if popup.slopeInterceptButton.isChecked():
            self.calibrationType = 1
            self.calibration = self.slopeInterceptCalibration
        elif popup.valuesButton.isChecked():
            self.calibrationType = 0
            self.calibration = self.twoValueCalibration

        self.unit = str(popup.unit.text())

    def delete(self):
        """Delete Widget."""

        self.deleteLater()

    def close(self):
        """Close the device."""

        if self.dm.getStatus() == False:
            self.dm.closeDevice(self.deviceID)
        else:
            popup = DoReallyDialog(self.tr("Warning"),
                self.tr("You have to stop the measurement to delete a device."))
            popup.exec_()


class DeviceSettingsDialog(QtGui.QDialog):
    """Settings dialog for device specific settings."""

    def __init__(self, deviceID, dm, parent=None):
        """

        :param deviceID: DeviceID
        :type deviceID: DeviceID
        :param dm: DeviceManager
        :type dm: DeviceManager

        """
        QtGui.QDialog.__init__(self, parent)
        qfile = QtCore.QFile(":/ui/deviceSettingsDialog.ui")
        qfile.open(QtCore.QIODevice.ReadOnly)
        self.ui = uic.loadUi(qfile, self)

        self.deviceID = deviceID
        self.dm = dm

        self.get1.clicked.connect(self.setCurrentValue1)
        self.get2.clicked.connect(self.setCurrentValue2)

    def setCurrentValue1(self):
        """Get current displayedValue from Device."""

        rv = self.dm.getLastRawValue(self.deviceID)
        self.is1.setValue(rv.getDisplayedValue())

    def setCurrentValue2(self):
        """Get current displayedValue from Device."""

        rv = self.dm.getLastRawValue(self.deviceID)
        self.is2.setValue(rv.getDisplayedValue())


class MainWindow(QtGui.QMainWindow):
    """Main window."""

    dm = None
    displayWidgets = {}

    running = False

    log = False
    tmpfile = None
    starttime = 0
    lasttime = 0
    loggingInterval = 3
    pathToLogFile = None

    officePath = None

    def __init__(self, parent=None):
        QtGui.QMainWindow.__init__(self, parent)
        qfile = QtCore.QFile(":/ui/mainWindow.ui")
        qfile.open(QtCore.QIODevice.ReadOnly)
        self.ui = uic.loadUi(qfile, self)

        self.measurementButton.clicked.connect(self.startStopMeasurement)
        self.loggingButton.clicked.connect(self.startStopLogging)
        self.saveButton.clicked.connect(self.saveLog)
        self.addDeviceButton.clicked.connect(self.addDevice)
        self.openButton.clicked.connect(self.openLog)

        self.actionSettings.triggered.connect(self.settingsDialog)
        self.actionDevicemanager.triggered.connect(self.devicemanagerDialog)

        self.dm = DeviceManager()
        self.timer = QtCore.QTimer()
        self.timer.timeout.connect(self.update)
        self.timer.start(50)

        self.settings = QtCore.QSettings()
        self.officePath = str(self.settings.value("office/path", "").toString())
        self.loggingInterval = int(self.settings.value("logging/interval", 1).toInt()[0])

    def settingsDialog(self):
        """Open a SettingsDialog."""

        popup = SettingsDialog()
        popup.exec_()

        self.officePath = str(self.settings.value("office/path", "").toString())
        self.loggingInterval = int(self.settings.value("logging/interval", 1).toInt()[0])

    def devicemanagerDialog(self):
        """Open a DevicemanagerDialog."""
        
        if self.dm.getStatus() == False:
            popup = DevicemanagerDialog(self.dm)
            popup.exec_()
        else:
            popup = DoReallyDialog(self.tr("Warning"),
                self.tr("You have to stop the measurement to open the devicemanager."))
            popup.exec_()

    def openLog(self):
        """Open last log with office."""
        
        import subprocess
        import os

        if self.pathToLogFile:
            subprocess.call('"' + self.officePath + '"' + ' ' + 
                '"' + self.pathToLogFile + '"', shell=True)
                    # FIXME: security flaw: shell=True 
        else:
            popup = DoReallyDialog(self.tr("Warning"),
                self.tr("You have not saved a log yet."))
            popup.exec_()

    def addDevice(self):
        """Open a NewDeviceDialog."""
        
        popup = NewDeviceDialog(self.dm)
        popup.exec_()

        if popup.result():
            device = str(popup.deviceComboBox.currentText())
            port = str(popup.portComboBox.currentText())

            if device == "XLS200":
                xls200Popup = Xls200Dialog()
                for i in (xls200Popup.subdevice1ComboBox,
                        xls200Popup.subdevice2ComboBox, xls200Popup.subdevice3ComboBox):
                    i.addItems([""] + self.dm.getValidDevices())

                xls200Popup.exec_()

                if xls200Popup.result():
                    xls200ID = self.dm.openWithConfig(DeviceConfig(device, port))
                    sub1 = str(xls200Popup.subdevice1ComboBox.currentText())
                    sub2 = str(xls200Popup.subdevice2ComboBox.currentText())
                    sub3 = str(xls200Popup.subdevice3ComboBox.currentText())
                    
                    if sub1 != "":
                            deviceID = self.dm.openWithConfig(DeviceConfig(sub1, xls200ID, 1))
                            sub1Widget = DisplayWidget(deviceID, self.dm)
                            self.verticalLayout.addWidget(sub1Widget)
                            self.displayWidgets[deviceID] = sub1Widget

                    if sub2 != "":
                            deviceID = self.dm.openWithConfig(DeviceConfig(sub2, xls200ID, 2))
                            sub2Widget = DisplayWidget(deviceID, self.dm)
                            self.verticalLayout.addWidget(sub2Widget)
                            self.displayWidgets[deviceID] = sub2Widget

                    if sub3 != "":
                            deviceID = self.dm.openWithConfig(DeviceConfig(sub3, xls200ID, 3))
                            sub3Widget = DisplayWidget(deviceID, self.dm)
                            self.verticalLayout.addWidget(sub3Widget)
                            self.displayWidgets[deviceID] = sub3Widget

            else:
                deviceID = self.dm.openWithConfig(DeviceConfig(device, port))
                deviceWidget = DisplayWidget(deviceID, self.dm)
                self.verticalLayout.addWidget(deviceWidget)
                self.displayWidgets[deviceID] = deviceWidget

    def startStopMeasurement(self):
        """Start/Stop measurement."""
        
        if self.dm.getStatus() == False:
            self.dm.start()
            self.running = True
            self.measurementButton.setText(self.tr("Stop"))

        elif self.dm.getStatus() == True:
            self.dm.stop()
            self.running = False
            self.measurementButton.setText(self.tr("Start"))

    def startStopLogging(self):
        """Start/Stop logging."""

        import time
        import tempfile

        if self.log == False:
            if self.tmpfile:
                popup = DoReallyDialog(self.tr("Overwrite last log"),
                    self.tr("Do you really want to overwrite the last (unsaved) log?\n")+
                    self.tr("If not, please cancel and save it first."))
                popup.exec_()

                if popup.result() == 0:
                    return

            self.tmpfile = tempfile.TemporaryFile()
            self.starttime = time.time()
            self.log = True
            self.loggingButton.setText(self.tr("Stop logging"))

        elif self.log:
            self.log = False
            self.loggingButton.setText(self.tr("Start logging"))

    def saveLog(self):
        """Save last log to file."""

        import os

        if self.tmpfile:
	        popup = QtGui.QFileDialog()
	        filename = QtGui.QFileDialog.getSaveFileName(self, self.tr("Save file"), os.path.expanduser("~"), "")

	        if filename[-4:] != ".csv":
	            filename += ".csv"

	        self.tmpfile.seek(0, 0)
	        with open(filename, 'w') as stream:
	            stream.write(self.tmpfile.read())
	        self.pathToLogFile = str(filename)
        else:
            popup = DoReallyDialog(self.tr("Warning"),
                self.tr("You first have to log something, to save it."))
            popup.exec_()

            if popup.result() == 0:
                return

    def update(self):
        """Update the displayWidgets and, when logging enabled log."""
        
        import time
        # python3 incompatibility: .iteritems()
        # Delete unnecessary widgets
        deviceIDsToBeDeleted = []
        for deviceID, widget in self.displayWidgets.iteritems():
            if deviceID not in self.dm.getAllDeviceIDs():
                deviceIDsToBeDeleted.append(deviceID)
        
        self.dm.closeEmptyMultiboxDevices()

        for i in deviceIDsToBeDeleted:
            try:
                self.displayWidgets[i].delete()
                del(self.displayWidgets[i])
            except KeyError:
                # Some devices don't have widgets (e.g. xls200), so there are no widgets to be deleted
                pass

        if self.running:
            # update widgets
            for deviceID, widget in self.displayWidgets.iteritems():
                unit = None
                if widget.unit != "":
                    unit = widget.unit

                rv = self.dm.getCalibratedLastRawValue(widget.deviceID, widget.calibration, widget.unit)
                widget.lcdNumber.display(rv.getDisplayedValue())
                widget.label.setText(str(rv.getFactor("prefix") + rv.getUnit()).decode('utf-8'))
                # python3 incompatibility: in python3 .decode() is not needed anymore
            
            # log    
            if self.log and ((time.time() - self.lasttime) > self.loggingInterval):
                for deviceID, widget in self.displayWidgets.iteritems():
                    unit = None
                    if widget.unit != "":
                        unit = widget.unit
                    rv = self.dm.getCalibratedLastRawValue(widget.deviceID, widget.calibration, widget.unit)
                    self.tmpfile.write(str(rv.getDisplayedValue() * rv.getFactor()) + ",")

                self.tmpfile.write("\n")
                self.lasttime = time.time()
        

class App(QtGui.QApplication):
    def __init__(self, *args, **kwargs):
        QtGui.QApplication.__init__(self, *args, **kwargs)
        self.connect(self, QtCore.SIGNAL("lastWindowClosed()"), self.byebye )

    def setup(self):
        self.main = MainWindow()
        self.main.show()

    def byebye(self):
        self.exit(0)

if __name__ == "__main__":
    app = App(sys.argv)

    QtCore.QCoreApplication.setOrganizationName("Lausen")
    QtCore.QCoreApplication.setOrganizationDomain("lausen.nl")
    QtCore.QCoreApplication.setApplicationName("MeasurementValueLogging")

    translator = QtCore.QTranslator()
    langVal = QtCore.QSettings().value("i18n", -1).toInt()[0]
    
    if langVal == -1:
        locale = QtCore.QLocale.system().name()
        if translator.load(":/i18n/" + locale + "qm"):
            app.installTranslator(translator)
    if langVal == 1:
        translator.load(":/i18n/de.qm")
        app.installTranslator(translator)

    app.setup()
    app.exec_()