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
        self.lineEdit = QtWidgets.QLineEdit(CalibrationDialog)
        self.lineEdit.setGeometry(QtCore.QRect(300, 152, 61, 26))
        self.lineEdit.setObjectName("lineEdit")
        self.lineEdit_2 = QtWidgets.QLineEdit(CalibrationDialog)
        self.lineEdit_2.setGeometry(QtCore.QRect(300, 182, 61, 26))
        self.lineEdit_2.setObjectName("lineEdit_2")
        self.pushButton = QtWidgets.QPushButton(CalibrationDialog)
        self.pushButton.setGeometry(QtCore.QRect(10, 306, 381, 27))
        self.pushButton.setObjectName("pushButton")
        self.label_9 = QtWidgets.QLabel(CalibrationDialog)
        self.label_9.setGeometry(QtCore.QRect(60, 230, 261, 18))
        font = QtGui.QFont()
        font.setPointSize(14)
        self.label_9.setFont(font)
        self.label_9.setAlignment(QtCore.Qt.AlignCenter)
        self.label_9.setObjectName("label_9")
        self.pushButton_2 = QtWidgets.QPushButton(CalibrationDialog)
        self.pushButton_2.setGeometry(QtCore.QRect(10, 273, 381, 27))
        self.pushButton_2.setObjectName("pushButton_2")

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
        self.pushButton.setText(_translate("CalibrationDialog", "Save Calibration"))
        self.label_9.setText(_translate("CalibrationDialog", "Scale = N/A"))
        self.pushButton_2.setText(_translate("CalibrationDialog", "Calculate"))


if __name__ == "__main__":
    import sys
    app = QtWidgets.QApplication(sys.argv)
    CalibrationDialog = QtWidgets.QDialog()
    ui = Ui_CalibrationDialog()
    ui.setupUi(CalibrationDialog)
    CalibrationDialog.show()
    sys.exit(app.exec_())
