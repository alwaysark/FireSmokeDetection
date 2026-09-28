# -*coding=utf-8
import sys
import logging

from PyQt5 import QtCore, QtWidgets

from uicontroller.Main_Window import MainWindow, StdOut


def enable_log():
    logging.basicConfig(level=logging.DEBUG, format='%(asctime)s - %(levelname)s - %(message)s')


def main():
    enable_log()
    # AA_EnableHighDpiScaling 必须在 QApplication 创建之前设置
    QtCore.QCoreApplication.setAttribute(QtCore.Qt.AA_EnableHighDpiScaling)
    app = QtWidgets.QApplication(sys.argv)

    # mainwindow 必须与 app.exec_() 处于同一作用域，
    # 否则函数返回后窗口引用丢失，会被垃圾回收直接销毁
    mainwindow = MainWindow()

    # 重定向 print 输出到主界面控制台
    stdout = StdOut()
    stdout.signalForText.connect(mainwindow.displayLog)
    sys.stdout = stdout
    sys.stderr = stdout

    mainwindow.show()
    sys.exit(app.exec_())


if __name__ == "__main__":
    main()
