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
        CalibrationDialog.resize(400, 339)
        CalibrationDialog.setWindowOpacity(1.0)
        self.label = QtWidgets.QLabel(CalibrationDialog)
        self.label.setGeometry(QtCore.QRect(10, 20, 371, 20))
        self.label.setObjectName("label")
        self.label_2 = QtWidgets.QLabel(CalibrationDialog)
        self.label_2.setGeometry(QtCore.QRect(10, 50, 371, 20))
        self.label_2.setObjectName("label_2")
        self.label_3 = QtWidgets.QLabel(CalibrationDialog)
        self.label_3.setGeometry(QtCore.QRect(10, 80, 381, 20))
        self.label_3.setObjectName("label_3")
        self.label_4 = QtWidgets.QLabel(CalibrationDialog)
        self.label_4.setGeometry(QtCore.QRect(10, 110, 371, 18))
        self.label_4.setObjectName("label_4")
        self.label_5 = QtWidgets.QLabel(CalibrationDialog)
        self.label_5.setGeometry(QtCore.QRect(250, 150, 41, 31))
        self.label_5.setObjectName("label_5")
        self.label_6 = QtWidgets.QLabel(CalibrationDialog)
        self.label_6.setGeometry(QtCore.QRect(250, 180, 41, 31))
        self.label_6.setObjectName("label_6")
        self.label_7 = QtWidgets.QLabel(CalibrationDialog)
        self.label_7.setGeometry(QtCore.QRect(40, 150, 41, 31))
        self.label_7.setObjectName("label_7")
        self.label_8 = QtWidgets.QLabel(CalibrationDialog)
        self.label_8.setGeometry(QtCore.QRect(40, 180, 41, 31))
        self.label_8.setObjectName("label_8")
        self.CalibX1_label = QtWidgets.QLabel(CalibrationDialog)
        self.CalibX1_label.setGeometry(QtCore.QRect(92, 156, 91, 18))
        font = QtGui.QFont()
        font.setPointSize(14)
        self.CalibX1_label.setFont(font)
        self.CalibX1_label.setObjectName("CalibX1_label")
        self.CalibX2_label = QtWidgets.QLabel(CalibrationDialog)
        self.CalibX2_label.setGeometry(QtCore.QRect(93, 186, 91, 18))
        font = QtGui.QFont()
        font.setPointSize(14)
        self.CalibX2_label.setFont(font)
        self.CalibX2_label.setObjectName("CalibX2_label")
        self.Wave1_edit = QtWidgets.QLineEdit(CalibrationDialog)
        self.Wave1_edit.setGeometry(QtCore.QRect(300, 152, 61, 26))
        self.Wave1_edit.setObjectName("Wave1_edit")
        self.Wave2_edit = QtWidgets.QLineEdit(CalibrationDialog)
        self.Wave2_edit.setGeometry(QtCore.QRect(300, 182, 61, 26))
        self.Wave2_edit.setObjectName("Wave2_edit")
        self.pushButton = QtWidgets.QPushButton(CalibrationDialog)
        self.pushButton.setEnabled(False)
        self.pushButton.setGeometry(QtCore.QRect(10, 306, 381, 27))
        self.pushButton.setObjectName("pushButton")
        self.NewScale_label = QtWidgets.QLabel(CalibrationDialog)
        self.NewScale_label.setGeometry(QtCore.QRect(10, 230, 381, 20))
        font = QtGui.QFont()
        font.setPointSize(14)
        self.NewScale_label.setFont(font)
        self.NewScale_label.setAlignment(QtCore.Qt.AlignCenter)
        self.NewScale_label.setObjectName("NewScale_label")
        self.CalculateScale_button = QtWidgets.QPushButton(CalibrationDialog)
        self.CalculateScale_button.setGeometry(QtCore.QRect(10, 273, 381, 27))
        self.CalculateScale_button.setObjectName("CalculateScale_button")

        self.retranslateUi(CalibrationDialog)
        QtCore.QMetaObject.connectSlotsByName(CalibrationDialog)

    def retranslateUi(self, CalibrationDialog):
        _translate = QtCore.QCoreApplication.translate
        CalibrationDialog.setWindowTitle(_translate("CalibrationDialog", "Calibration"))
        self.label.setText(_translate("CalibrationDialog", "Step1. Select first calibration line from plot"))
        self.label_2.setText(_translate("CalibrationDialog", "Step2. Assign first wavelength"))
        self.label_3.setText(_translate("CalibrationDialog", "Step 3. Select second calibration line from plot"))
        self.label_4.setText(_translate("CalibrationDialog", "Step 4. Assign second wavelength"))
        self.label_5.setText(_translate("CalibrationDialog", "<html><head/><body><p><span style=\" font-size:14pt;\">λ</span><span style=\" font-size:14pt; vertical-align:sub;\">1</span><span style=\" font-size:14pt;\">=</span></p></body></html>"))
        self.label_6.setText(_translate("CalibrationDialog", "<html><head/><body><p><span style=\" font-size:14pt;\">λ</span><span style=\" font-size:14pt; vertical-align:sub;\">2</span><span style=\" font-size:14pt;\">=</span></p></body></html>"))
        self.label_7.setText(_translate("CalibrationDialog", "<html><head/><body><p><span style=\" font-size:14pt;\">X<sub>1</sub>=</span></p></body></html>"))
        self.label_8.setText(_translate("CalibrationDialog", "<html><head/><body><p><span style=\" font-size:14pt;\">X<sub>2</sub>=</span></p></body></html>"))
        self.CalibX1_label.setText(_translate("CalibrationDialog", "not set"))
        self.CalibX2_label.setText(_translate("CalibrationDialog", "not set"))
        self.pushButton.setText(_translate("CalibrationDialog", "Update Scale"))
        self.NewScale_label.setText(_translate("CalibrationDialog", "Scaler = N/A"))
        self.CalculateScale_button.setText(_translate("CalibrationDialog", "Calculate"))


if __name__ == "__main__":
    import sys
    app = QtWidgets.QApplication(sys.argv)
    CalibrationDialog = QtWidgets.QDialog()
    ui = Ui_CalibrationDialog()
    ui.setupUi(CalibrationDialog)
    CalibrationDialog.show()
    sys.exit(app.exec_())
