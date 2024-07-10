import argparse  # 导入argparse模块，用于从命令行解析参数
import cgitb  # 导入cgitb模块，用于提供更详细的traceback信息
import logging  # 导入logging模块，用于记录日志
import os  # 导入os模块，用于与操作系统交互
import sys  # 导入sys模块，用于访问与Python解释器相关的变量和函数
from PyQt5 import QtCore,QtWidgets  # 从PyQt5模块导入QtWidgets，用于创建图形用户界面(GUI)

# from UI.FireSmokeDetection import Ui_MainWindow  # 从UI.FireSmokeDetection模块导入Ui_MainWindow类，这是你的主窗口界面
from uicontroller.Main_Window import MainWindow, StdOut

class HomeController():

    def __init__(self):  # 定义构造函数
        super().__init__()  # 调用父类的构造函数

        # 创建日志目录
        log_dir = os.path.join(os.getcwd(), 'log')
        os.makedirs(log_dir, exist_ok=True)

        # 启用 cgitb 模块，提供详细的错误信息
        cgitb.enable(format='text', logdir=log_dir)

        # 解析命令行参数
        opt = self.parse_opt()

        # 运行主程序
        self.run(vars(opt))

    def run(self, options):  # 定义一个名为run的函数，接受任意数量的关键字参数
        # 初始化 GUI
        QtCore.QCoreApplication.setAttribute(QtCore.Qt.AA_EnableHighDpiScaling)  # 启用高分辨率缩放
        # app = QtWidgets.QApplication(sys.argv)  # 创建一个QApplication实例
        mainwindow = MainWindow()  # 创建一个MainWindow实例

        # 重定向 stdout
        stdout = StdOut()  # 创建一个StdOut实例
        stdout.signalForText.connect(mainwindow.displayLog)  # 将StdOut实例的signalForText信号连接到mainwindow的displayLog槽
        sys.stdout = stdout  # 将系统的标准输出重定向到我们创建的StdOut实例
        sys.stderr = stdout  # 将系统的标准错误重定向到我们创建的StdOut实例
        logging.StreamHandler(stdout)  # 创建一个StreamHandler实例，将日志输出到我们创建的StdOut实例

        # 显示主窗口
        mainwindow.show()  # 显示mainwindow实例
        # sys.exit(app.exec_())  # 进入事件循环，等待用户操作，当窗口被关闭时，结束程序

    # 解析命令行参数
    def parse_opt(self):  # 定义一个名为parse_opt的方法，用于解析命令行参数
        parser = argparse.ArgumentParser()  # 创建一个ArgumentParser实例
        # 添加各种命令行参数
        parser.add_argument('--weights', type=str,
                            default='need/models/best.onnx')  # 添加一个名为weights的参数，类型为str，默认值为'need/models/yolov8-tiny.onnx'
        parser.add_argument('--classes', type=str,
                            default='need/best.txt')  # 添加一个名为classes的参数，类型为str，默认值为'need/yolov8-tiny.txt'
        parser.add_argument('--source', type=str, default='data')  # 添加一个名为source的参数，类型为str，默认值为'data'
        parser.add_argument('--imgsz', nargs='+', type=int, default=[640],
                            help='inference size w,h')  # 添加一个名为imgsz的参数，类型为int，默认值为[640]，帮助信息为'inference size w,h'
        parser.add_argument('--conf_thres', type=float, default=0.5)  # 添加一个名为conf_thres的参数，类型为float，默认值为0.5
        parser.add_argument('--iou_thres', type=float, default=0.5)  # 添加一个名为iou_thres的参数，类型为float，默认值为0.5
        parser.add_argument('--save_path', type=str, default='out')  # 添加一个名为save_path的参数，类型为str，默认值为'out'
        parser.add_argument('--save_log', action='store_true')  # 添加一个名为save_log的参数，如果在命令行中出现这个参数，那么其值为True，否则为False
        parser.add_argument('--save_result',
                            action='store_true')  # 添加一个名为save_result的参数，如果在命令行中出现这个参数，那么其值为True，否则为False
        parser.add_argument('--video_split',
                            action='store_true')  # 添加一个名为video_split的参数，如果在命令行中出现这个参数，那么其值为True，否则为False
        opt_ = parser.parse_args()  # 解析命令行参数，并将结果保存到opt_变量中
        opt_.imgsz *= 2 if len(opt_.imgsz) == 1 else 1  # 如果imgsz只有一个元素，那么将其值乘以2，否则不变
        return opt_  # 返回opt_
