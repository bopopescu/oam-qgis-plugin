# -*- coding: utf-8 -*-
"""
/***************************************************************************
 OpenAerialMapDialog
                                 A QGIS plugin
 This plugin can be used as an OAM client to browse, search, download and
 upload imagery from/to the OAM catalog.
                             -------------------
        begin                : 2015-07-01
        git sha              : $Format:%H$
        copyright            : (C) 2015 by Humanitarian OpenStreetMap Team (HOT)
        email                : tassia@acaia.ca  / yoji.salut@gmail.com
 ***************************************************************************/

/***************************************************************************
 *                                                                         *
 *   This program is free software; you can redistribute it and/or modify  *
 *   it under the terms of the GNU General Public License as published by  *
 *   the Free Software Foundation; either version 2 of the License, or     *
 *   (at your option) any later version.                                   *
 *                                                                         *
 ***************************************************************************/
"""

import os, sys

from PyQt4 import QtGui, uic
from PyQt4.Qt import *

from qgis.gui import QgsMessageBar
from qgis.core import QgsMapLayer, QgsMessageLog
from osgeo import gdal, osr
import json
import time
import math, imghdr


FORM_CLASS, _ = uic.loadUiType(os.path.join(
    os.path.dirname(__file__), 'ui/setting_dialog.ui'))

class SettingDialog(QtGui.QDialog, FORM_CLASS):

    def __init__(self, iface, settings, parent=None):
        """Constructor."""
        super(SettingDialog, self).__init__(parent)
        # Set up the user interface from Designer.
        # After setupUI you can access any designer object by doi, self.settingsng
        # self.<objectname>, and you can use autoconnect slots - see
        # http://qt-project.org/doc/qt-4.8/designer-using-a-ui-file.html
        # #widgets-and-dialogs-with-auto-connect
        self.iface = iface
        self.setupUi(self)

        self.settings = settings

        #register event handlers
        self.buttonBox.button(QtGui.QDialogButtonBox.Cancel).clicked.connect(self.cancel)
        self.buttonBox.button(QtGui.QDialogButtonBox.Save).clicked.connect(self.saveSettings)

        #set the calendars
        self.sense_start_edit.setCalendarPopup(1)
        self.sense_start_edit.setDisplayFormat('dd.MM.yyyy HH:mm')
        self.sense_end_edit.setCalendarPopup(1)
        self.sense_end_edit.setDisplayFormat('dd.MM.yyyy HH:mm')

        #event handler for bucket name input
        self.storage_combo_box.currentIndexChanged.connect(self.enableSpecify)

        #initialize
        self.loadSettings()

    def loadSettings(self):
        self.loadMetadataSettings()
        self.loadStorageSettings()
        self.loadOptionsSettings()

    def saveSettings(self):
        self.saveMetadataSettings()
        self.saveStorageSettings()
        self.saveOptionsSettings()

    def cancel(self):
        #close the Dialog
        pass

    def saveMetadataSettings(self):
        self.settings.beginGroup("Metadata")
        self.settings.setValue('TITLE', self.title_edit.text())
        self.settings.setValue('PLATFORM', self.platform_combo_box.currentIndex())
        self.settings.setValue('SENSOR', self.sensor_edit.text())

        self.settings.setValue('SENSE_START', self.sense_start_edit.dateTime())
        self.settings.setValue('SENSE_END', self.sense_end_edit.dateTime())
        #make sure about TAGS
        self.settings.setValue('TAGS', self.tags_edit.text())

        print repr(self.settings.value('SENSE_START'))
        print repr(self.settings.value('SENSE_END'))
        #make sure about TAGS
        print repr(self.settings.value('TAGS'))

        self.settings.setValue('PROVIDER', self.provider_edit.text())
        self.settings.setValue('CONTACT', self.contact_edit.text())
        self.settings.setValue('WEBSITE', self.website_edit.text())

        """probably need to reorganize this part"""
        self.settings.setValue('LICENSE', self.license_check_box.isChecked())
        self.settings.setValue('REPROJECT', self.reproject_check_box.isChecked())

        self.settings.endGroup()

    def saveOptionsSettings(self):

        self.settings.beginGroup("Options")
        self.settings.setValue('NOTIFY_OAM', self.notify_oam_check.isChecked())
        self.settings.setValue('TRIGGER_OAM_TS', self.trigger_tiling_check.isChecked())
        self.settings.endGroup()

    def saveStorageSettings(self):

        self.settings.beginGroup("Storage")
        if self.storage_combo_box.currentIndex() == 0:
            self.settings.setValue('S3_BUCKET_NAME', 'oam-qgis-plugin-test')
        else:
            self.settings.setValue('S3_BUCKET_NAME', self.specify_edit.text())
        self.settings.setValue('AWS_ACCESS_KEY_ID', self.key_id_edit.text())
        self.settings.setValue('AWS_SECRET_ACCESS_KEY', self.secret_key_edit.text())
        self.settings.endGroup()

    def loadMetadataSettings(self):
        self.settings.beginGroup("Metadata")
        self.title_edit.setText(self.settings.value('TITLE'))
        if self.settings.value('PLATFORM') == None:
            self.title_edit.setCursorPosition(0)
        else:
            self.platform_combo_box.setCurrentIndex(int(self.settings.value('PLATFORM')))
        self.sensor_edit.setText(self.settings.value('SENSOR'))
        self.sensor_edit.setCursorPosition(0)

        self.sense_start_edit.setDateTime(QDateTime(self.settings.value('SENSE_START')))
        self.sense_end_edit.setDateTime(QDateTime(self.settings.value('SENSE_END')))

        #make sure about TAGS
        if self.settings.value('TAGS') == None:
            self.tags_edit.setText(', '.join(''))
        else:
            self.tags_edit.setText(', '.join(self.settings.value('TAGS')))
        self.tags_edit.setCursorPosition(0)

        self.provider_edit.setText(self.settings.value('PROVIDER'))
        self.provider_edit.setCursorPosition(0)
        self.contact_edit.setText(self.settings.value('CONTACT'))
        self.contact_edit.setCursorPosition(0)
        self.website_edit.setText(self.settings.value('WEBSITE'))
        self.website_edit.setCursorPosition(0)

        """
        Boolean values are converted into string and lower case for
        'if' statement, since PyQt sometimes returns 'true', just like C++,
        instead of 'True', Python style.
        Maybe we can use integer values (0 or 1), instead of using string.
        """
        print str(self.settings.value('LICENSE'))
        print str(self.settings.value('REPROJECT'))

        if str(self.settings.value('LICENSE')).lower() == 'true':
            self.license_check_box.setCheckState(2)

        if str(self.settings.value('REPROJECT')).lower() == 'true':
            self.reproject_check_box.setCheckState(2)

        self.settings.endGroup()

    def loadOptionsSettings(self):
        self.settings.beginGroup("Options")

        """
        Boolean values are converted into string and lower case for
        'if' statement, since PyQt sometimes returns 'true', just like C++,
        instead of 'True', Python style.
        Maybe we can use integer values (0 or 1), instead of using string.
        """
        print str(self.settings.value('NOTIFY_OAM'))
        print str(self.settings.value('TRIGGER_OAM_TS'))

        if str(self.settings.value('NOTIFY_OAM')).lower() == 'true':
            self.notify_oam_check.setCheckState(2)
        if str(self.settings.value('TRIGGER_OAM_TS')).lower() == 'true':
            self.trigger_tiling_check.setCheckState(2)

        self.settings.endGroup()

    def loadStorageSettings(self):
        self.settings.beginGroup("Storage")
        bucket = self.settings.value('S3_BUCKET_NAME')
        storage_index = self.storage_combo_box.findText(bucket,Qt.MatchExactly)
        if not storage_index == -1:
            self.storage_combo_box.setCurrentIndex(storage_index)
        else:
            self.storage_combo_box.setCurrentIndex(self.storage_combo_box.findText(self.tr('other...')))
            self.specify_label.setEnabled(1)
            self.specify_edit.setEnabled(1)
            self.specify_edit.setText(self.settings.value('S3_BUCKET_NAME'))
        self.key_id_edit.setText(self.settings.value('AWS_ACCESS_KEY_ID'))
        self.key_id_edit.setCursorPosition(0)
        self.secret_key_edit.setText(self.settings.value('AWS_SECRET_ACCESS_KEY'))
        self.secret_key_edit.setCursorPosition(0)
        self.settings.endGroup()

    def enableSpecify(self):
        if self.storage_combo_box.currentIndex() == 1:
            self.specify_label.setEnabled(1)
            self.specify_edit.setEnabled(1)
        else:
            self.specify_label.setEnabled(0)
            self.specify_edit.setText('')
            self.specify_edit.setEnabled(0)
