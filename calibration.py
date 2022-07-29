# -*- coding: utf-8 -*-

# Form implementation generated from reading ui file 'calibration.ui'
#
# Created by: PyQt5 UI code generator 5.12.3
#
# WARNING! All changes made in this file will be lost!


from PyQt5 import QtCore, QtGui, QtWidgets


class Ui_CalibrationDialog(object):
    def setupUi(self, CalibrationDialog):
        CalibrationDialog.setObjectName("CalibrationDialog")
        CalibrationDialog.setWindowModality(QtCore.Qt.NonModal)
        CalibrationDialog.resize(400, 409)
        CalibrationDialog.setWindowOpacity(1.0)
        self.label = QtWidgets.QLabel(CalibrationDialog)
        self.label.setGeometry(QtCore.QRect(10, 80, 371, 20))
        self.label.setObjectName("label")
        self.label_2 = QtWidgets.QLabel(CalibrationDialog)
        self.label_2.setGeometry(QtCore.QRect(10, 110, 371, 20))
        self.label_2.setObjectName("label_2")
        self.label_3 = QtWidgets.QLabel(CalibrationDialog)
        self.label_3.setGeometry(QtCore.QRect(10, 140, 381, 20))
        self.label_3.setObjectName("label_3")
        self.label_4 = QtWidgets.QLabel(CalibrationDialog)
        self.label_4.setGeometry(QtCore.QRect(10, 170, 371, 18))
        self.label_4.setObjectName("label_4")
        self.label_5 = QtWidgets.QLabel(CalibrationDialog)
        self.label_5.setGeometry(QtCore.QRect(250, 210, 41, 31))
        self.label_5.setObjectName("label_5")
        self.label_6 = QtWidgets.QLabel(CalibrationDialog)
        self.label_6.setGeometry(QtCore.QRect(250, 240, 41, 31))
        self.label_6.setObjectName("label_6")
        self.label_7 = QtWidgets.QLabel(CalibrationDialog)
        self.label_7.setGeometry(QtCore.QRect(40, 210, 41, 31))
        self.label_7.setObjectName("label_7")
        self.label_8 = QtWidgets.QLabel(CalibrationDialog)
        self.label_8.setGeometry(QtCore.QRect(40, 240, 41, 31))
        self.label_8.setObjectName("label_8")
        self.CalibX1_label = QtWidgets.QLabel(CalibrationDialog)
        self.CalibX1_label.setGeometry(QtCore.QRect(92, 216, 91, 18))
        font = QtGui.QFont()
        font.setPointSize(14)
        self.CalibX1_label.setFont(font)
        self.CalibX1_label.setObjectName("CalibX1_label")
        self.CalibX2_label = QtWidgets.QLabel(CalibrationDialog)
        self.CalibX2_label.setGeometry(QtCore.QRect(93, 246, 91, 18))
        font = QtGui.QFont()
        font.setPointSize(14)
        self.CalibX2_label.setFont(font)
        self.CalibX2_label.setObjectName("CalibX2_label")
        self.Wave1_edit = QtWidgets.QLineEdit(CalibrationDialog)
        self.Wave1_edit.setGeometry(QtCore.QRect(300, 212, 61, 26))
        self.Wave1_edit.setAlignment(QtCore.Qt.AlignCenter)
        self.Wave1_edit.setObjectName("Wave1_edit")
        self.Wave2_edit = QtWidgets.QLineEdit(CalibrationDialog)
        self.Wave2_edit.setGeometry(QtCore.QRect(300, 242, 61, 26))
        self.Wave2_edit.setAlignment(QtCore.Qt.AlignCenter)
        self.Wave2_edit.setObjectName("Wave2_edit")
        self.UpdateScale_button = QtWidgets.QPushButton(CalibrationDialog)
        self.UpdateScale_button.setEnabled(False)
        self.UpdateScale_button.setGeometry(QtCore.QRect(10, 370, 381, 27))
        self.UpdateScale_button.setObjectName("UpdateScale_button")
        self.NewScale_label = QtWidgets.QLabel(CalibrationDialog)
        self.NewScale_label.setGeometry(QtCore.QRect(11, 291, 161, 20))
        font = QtGui.QFont()
        font.setPointSize(14)
        self.NewScale_label.setFont(font)
        self.NewScale_label.setAlignment(QtCore.Qt.AlignCenter)
        self.NewScale_label.setObjectName("NewScale_label")
        self.CalculateScale_button = QtWidgets.QPushButton(CalibrationDialog)
        self.CalculateScale_button.setGeometry(QtCore.QRect(10, 330, 381, 27))
        self.CalculateScale_button.setObjectName("CalculateScale_button")
        self.NewScale_rollbox = QtWidgets.QDoubleSpinBox(CalibrationDialog)
        self.NewScale_rollbox.setGeometry(QtCore.QRect(177, 284, 76, 31))
        font = QtGui.QFont()
        font.setPointSize(14)
        self.NewScale_rollbox.setFont(font)
        self.NewScale_rollbox.setProperty("value", 2.85)
        self.NewScale_rollbox.setObjectName("NewScale_rollbox")
        self.label_9 = QtWidgets.QLabel(CalibrationDialog)
        self.label_9.setGeometry(QtCore.QRect(264, 290, 121, 21))
        font = QtGui.QFont()
        font.setPointSize(14)
        self.label_9.setFont(font)
        self.label_9.setObjectName("label_9")
        self.label_10 = QtWidgets.QLabel(CalibrationDialog)
        self.label_10.setGeometry(QtCore.QRect(100, 40, 41, 31))
        self.label_10.setObjectName("label_10")
        self.nm0_edit = QtWidgets.QLineEdit(CalibrationDialog)
        self.nm0_edit.setGeometry(QtCore.QRect(150, 41, 61, 26))
        self.nm0_edit.setAlignment(QtCore.Qt.AlignCenter)
        self.nm0_edit.setObjectName("nm0_edit")
        self.label_11 = QtWidgets.QLabel(CalibrationDialog)
        self.label_11.setGeometry(QtCore.QRect(10, 10, 371, 18))
        self.label_11.setObjectName("label_11")
        self.nm0Set_button = QtWidgets.QPushButton(CalibrationDialog)
        self.nm0Set_button.setGeometry(QtCore.QRect(217, 40, 51, 27))
        self.nm0Set_button.setObjectName("nm0Set_button")

        self.retranslateUi(CalibrationDialog)
        QtCore.QMetaObject.connectSlotsByName(CalibrationDialog)

    def retranslateUi(self, CalibrationDialog):
        _translate = QtCore.QCoreApplication.translate
        CalibrationDialog.setWindowTitle(_translate("CalibrationDialog", "Calibration"))
        self.label.setText(_translate("CalibrationDialog", "Step 2. Select first calibration line from plot"))
        self.label_2.setText(_translate("CalibrationDialog", "Step 3. Assign first wavelength"))
        self.label_3.setText(_translate("CalibrationDialog", "Step 4. Select second calibration line from plot"))
        self.label_4.setText(_translate("CalibrationDialog", "Step 5. Assign second wavelength"))
        self.label_5.setText(_translate("CalibrationDialog", "<html><head/><body><p><span style=\" font-size:14pt;\">λ</span><span style=\" font-size:14pt; vertical-align:sub;\">1</span><span style=\" font-size:14pt;\">=</span></p></body></html>"))
        self.label_6.setText(_translate("CalibrationDialog", "<html><head/><body><p><span style=\" font-size:14pt;\">λ</span><span style=\" font-size:14pt; vertical-align:sub;\">2</span><span style=\" font-size:14pt;\">=</span></p></body></html>"))
        self.label_7.setText(_translate("CalibrationDialog", "<html><head/><body><p><span style=\" font-size:14pt;\">X<sub>1</sub>=</span></p></body></html>"))
        self.label_8.setText(_translate("CalibrationDialog", "<html><head/><body><p><span style=\" font-size:14pt;\">X<sub>2</sub>=</span></p></body></html>"))
        self.CalibX1_label.setText(_translate("CalibrationDialog", "not set"))
        self.CalibX2_label.setText(_translate("CalibrationDialog", "not set"))
        self.UpdateScale_button.setText(_translate("CalibrationDialog", "Update Scale & Reference"))
        self.NewScale_label.setText(_translate("CalibrationDialog", "New Scale ="))
        self.CalculateScale_button.setText(_translate("CalibrationDialog", "Calculate"))
        self.label_9.setText(_translate("CalibrationDialog", "pixels/nm"))
        self.label_10.setText(_translate("CalibrationDialog", "<html><head/><body><p><span style=\" font-size:14pt;\">λ</span><span style=\" font-size:14pt; vertical-align:sub;\">0</span><span style=\" font-size:14pt;\">=</span></p></body></html>"))
        self.nm0_edit.setText(_translate("CalibrationDialog", "410"))
        self.label_11.setText(_translate("CalibrationDialog", "Step 1. Set the reference wavelength"))
        self.nm0Set_button.setText(_translate("CalibrationDialog", "Set"))
