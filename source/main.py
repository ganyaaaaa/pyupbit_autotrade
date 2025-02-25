# -*- coding: utf-8 -*-

# Form implementation generated from reading ui file 'source/main.ui'
#
# Created by: PyQt5 UI code generator 5.15.11
#
# WARNING: Any manual changes made to this file will be lost when pyuic5 is
# run again.  Do not edit this file unless you know what you are doing.


from PyQt5 import QtCore, QtGui, QtWidgets


class Ui_MainWindow(object):
    def setupUi(self, MainWindow):
        MainWindow.setObjectName("MainWindow")
        MainWindow.resize(1000, 700)
        self.centralwidget = QtWidgets.QWidget(MainWindow)
        self.centralwidget.setObjectName("centralwidget")
        self.gridLayout = QtWidgets.QGridLayout(self.centralwidget)
        self.gridLayout.setObjectName("gridLayout")
        self.label_ticker = QtWidgets.QLabel(self.centralwidget)
        self.label_ticker.setObjectName("label_ticker")
        self.gridLayout.addWidget(self.label_ticker, 0, 0, 1, 1)
        self.input_ticker = QtWidgets.QLineEdit(self.centralwidget)
        self.input_ticker.setObjectName("input_ticker")
        self.gridLayout.addWidget(self.input_ticker, 0, 1, 1, 1)
        self.label_budget = QtWidgets.QLabel(self.centralwidget)
        self.label_budget.setObjectName("label_budget")
        self.gridLayout.addWidget(self.label_budget, 1, 0, 1, 1)
        self.input_budget = QtWidgets.QLineEdit(self.centralwidget)
        self.input_budget.setObjectName("input_budget")
        self.gridLayout.addWidget(self.input_budget, 1, 1, 1, 1)
        self.start_btn = QtWidgets.QPushButton(self.centralwidget)
        self.start_btn.setObjectName("start_btn")
        self.gridLayout.addWidget(self.start_btn, 2, 0, 1, 1)
        self.stop_btn = QtWidgets.QPushButton(self.centralwidget)
        self.stop_btn.setObjectName("stop_btn")
        self.gridLayout.addWidget(self.stop_btn, 2, 1, 1, 1)
        self.log_text = QtWidgets.QTextEdit(self.centralwidget)
        self.log_text.setReadOnly(True)
        self.log_text.setObjectName("log_text")
        self.log_text.setMinimumHeight(200)
        self.gridLayout.addWidget(self.log_text, 3, 0, 1, 2)
        MainWindow.setCentralWidget(self.centralwidget)
        self.statusbar = QtWidgets.QStatusBar(MainWindow)
        self.statusbar.setObjectName("statusbar")
        MainWindow.setStatusBar(self.statusbar)

        self.retranslateUi(MainWindow)
        QtCore.QMetaObject.connectSlotsByName(MainWindow)

    def retranslateUi(self, MainWindow):
        _translate = QtCore.QCoreApplication.translate
        MainWindow.setWindowTitle(_translate("MainWindow", "업비트 자동매매 프로그램"))
        self.label_ticker.setText(_translate("MainWindow", "매매할 종목 (예: KRW-BTC):"))
        self.label_budget.setText(_translate("MainWindow", "투자 금액 (KRW):"))
        self.start_btn.setText(_translate("MainWindow", "자동매매 시작"))
        self.stop_btn.setText(_translate("MainWindow", "자동매매 정지"))


if __name__ == "__main__":
    import sys
    app = QtWidgets.QApplication(sys.argv)
    MainWindow = QtWidgets.QMainWindow()
    ui = Ui_MainWindow()
    ui.setupUi(MainWindow)
    MainWindow.show()
    sys.exit(app.exec_())