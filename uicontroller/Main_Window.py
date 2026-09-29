# -*coding=utf-8

import logging  # 导入日志模块
import os  # 导入操作系统模块
import sys  # 导入系统模块
import time  # 导入时间模块
from datetime import datetime  # 从datetime模块导入datetime类

import cv2  # 导入OpenCV库
import numpy  # 导入NumPy库
from PyQt5 import QtCore, QtWidgets, QtGui  # 从PyQt5库导入QtCore, QtWidgets, QtGui模块
from PyQt5.QtWidgets import QMessageBox, QFileDialog, QFontDialog, QApplication  # 从PyQt5.QtWidgets模块导入QMessageBox, QFileDialog类

from utils import detect, general  # 从utils模块导入detect, general
from UI import FireSmokeDetection # 从utils.resource模块导入Yolo2onnx_detect_Demo_UI, resource_rc
from utils.utils import playAudio, setIsFlasg # 播放警报
# resource_rc.qInitResources()  # 初始化资源


class StdOut(QtCore.QObject):
    """重写sys.Stdout"""
    signalForText = QtCore.pyqtSignal(str)  # 定义一个信号

    def write(self, text):
        if text == '\n': return  # 如果文本是换行符，则返回
        if not isinstance(text, str): text = str(text)  # 如果文本不是字符串，则将其转换为字符串
        if len(text) > 500: text = text[0:10] + ' ...... ' + text[-10:-1]  # 如果文本长度大于500，则截取前10个和后10个字符
        self.signalForText.emit(text)  # 发送信号

    def flush(self):
        pass  # 刷新操作，这里不做任何操作

class DetectThread(QtCore.QThread):
    """检测线程"""
    img_sig = QtCore.pyqtSignal(numpy.ndarray)  # 定义一个信号，用于发送图像
    res_sig = QtCore.pyqtSignal(dict)  # 定义一个信号，用于发送结果

    def __init__(self, model: detect.YOLOv5 = None, dataset: detect.DataLoader = None):
        super(DetectThread, self).__init__()  # 调用父类构造函数
        #self.is_pause = False  # 初始化暂停标志为False
        self.is_running = False  # 初始化运行标志为False
        self.is_detecting = False  # 初始化检测标志为False
        self.model = model  # 初始化模型
        self.dataset: detect.DataLoader = dataset  # 初始化数据集
        self.display_fps = True  # 初始化显示帧数标志为True
        self.print_result = True  # 初始化打印结果标志为True

    def stopThread(self):
        if not self.is_running:  # 如果线程没有运行，直接返回
            return
        self.is_running = False  # 设置运行标志为False
        self.is_detecting = False  # 设置检测标志为False

    def stopDetect(self):
        if not self.is_detecting:  # 如果没有在检测，直接返回
            return
        self.is_detecting = False  # 设置检测标志为False

    def startThread(self):
        if self.is_running:  # 如果线程正在运行，直接返回
            return
        self.is_detecting = False  # 设置检测标志为False
        self.is_running = True  # 设置运行标志为True
        if not self.isRunning():  # 如果线程没有运行
            self.start()  # 启动线程

    def startDetect(self):
        if self.is_detecting:  # 如果正在检测，直接返回
            return
        self.is_detecting = True  # 设置检测标志为True
        self.is_running = True  # 设置运行标志为True
        if not self.isRunning():  # 如果线程没有运行
            self.start()  # 启动线程

    # def pauseDetect(self):
    #     self.is_pause = True  # 设置暂停标志为True

    def main(self):  # 主函数
        i = 0
        fps = '--'  # 初始化帧数为'--'
        fps_count = 0  # 初始化帧数计数为0
        t = time.time()  # 获取当前时间
        for img, path in self.dataset:  # 遍历数据集
            if not self.is_running:  # 如果线程没有运行，跳出循环
                break
            res = {}  # 初始化结果为空字典
            if self.is_detecting:  # 如果正在检测
                try:
                    res = self.model.detect(img)  # 使用模型检测图像
                    if self.print_result:  # 如果打印结果标志为True
                        print(res)  # 打印结果
                    # if self.print_bofang:  # 播放警报
                    if 'fire' in res:
                        i = i + 1
                        if i == 20:
                            playAudio()
                            i = 0
                    # else:
                    #     print("未检测到火焰")
                        # 播放警报
                except Exception as e:  # 捕获异常
                    print(e)  # 打印异常
                    self.is_detecting = False  # 设置检测标志为False
                    print('stop')  # 打印'stop'

            # 显示帧数
            ted = time.time() - t  # 计算时间差
            if ted >= 2:  # 如果时间差大于等于2
                fps = '%.1f' % (fps_count / ted)  # 计算帧数
                fps_count = 0  # 重置帧数计数
                t = time.time()  # 重新获取当前时间
            else:
                fps_count += 1  # 帧数计数加1
            if self.display_fps and not self.dataset.is_image:  # 如果显示帧数标志为True并且数据集不是图像
                fps_ = f'FPS:{fps}'  # 格式化帧数字符串
                lw = max(round(sum(img.shape) / 2 * 0.003), 2)  # 计算线宽
                tf = max(lw - 1, 1)  # 计算字体厚度
                h = cv2.getTextSize(fps_, 0, lw / 3, tf)[0][1]  # 获取文本高度
                cv2.putText(img, fps_, (10, 10 + h), 0, lw / 3, (255, 0, 0), tf, cv2.LINE_AA)  # 在图像上绘制文本

            self.img_sig.emit(img)  # 发送图像信号
            self.res_sig.emit(res)  # 发送结果信号
            # time.sleep(0.0001)

        print(f'"{self.dataset.source}" finished.')  # 打印数据集源已完成
        del self.dataset  # 删除数据集
        self.stopThread()  # 停止线程

    def run(self) -> None:
        try:
            self.main()  # 调用主函数
        except Exception as e:  # 捕获异常
            logging.exception(e)  # 记录异常

# noinspection PyAttributeOutsideInit
class MainWindow(QtWidgets.QMainWindow, FireSmokeDetection.Ui_MainWindow):
    def __init__(self):
        # 在这个方法中，一些初始化的操作被执行，包括设置UI，连接回调函数，初始化参数，安装事件过滤器，初始化检测线程，初始化脚本API，加载配置等。
        super(MainWindow, self).__init__()

        # setup ui, connect callback
        # 设置UI，连接回调函数
        self.setupUi(self)
        #self.statusBar().showMessage('initializing...')
        self.UI()
        # self.animation()

        # init params
        # 初始化参数
        self.save_video = False             # 正在录制标志位
        self.source = ''                    # 当前输入源：'0'（摄像头）、文件路径、'screen'（屏幕捕获）
        self.flip_type = (None, 1, 0, -1)   # 翻转下拉框的“索引→参数”映射元组：None不翻转、1水平、0垂直、-1双向
        # 旋转下拉框的“索引→参数”映射元组
        self.rotate_type = (None, cv2.ROTATE_90_CLOCKWISE, cv2.ROTATE_90_COUNTERCLOCKWISE, cv2.ROTATE_180)
        self.video_writer: cv2.VideoWriter      #类型注解，没有创建对象。告诉IDE这个成员将来会是 VideoWriter 类型，为的是以后写代码ide会自动补全
        self.box_color = (255, 0, 0)
        self.font = QtGui.QFont("Arial", 9)  # 默认字体设置为Arial，大小9

        # 安装事件过滤器
        self.installEventFilter(self)
        # self.textEdit.installEventFilter(self)
        # self.textEdit_2.installEventFilter(self)

        # 初始化检测线程
        self.dt = DetectThread()
        self.dt.img_sig.connect(self.displayImg)
        self.dt.finished.connect(self.stop)


        self.loadConfig()


# ==================== 绑定信号和槽（全部 connect 都在这里） ====================
    def UI(self):
        # 选择媒体文件，开始和停止检测，保存日志，保存截图，保存视频，更改类别，显示类别个数，打开保存目录，导入自定义脚本，更改输入配置，
        # 更改锚框颜色，锁定切换，清空控制台，重置输入源等。
        self.BaoCunLuJing.clicked.connect(self.changeOutputPath)  # 选择保存位置
        self.WenJianLuJing.clicked.connect(lambda: self.changeMediaFile(None))  # 选择媒体文件
        self.QuanZhongLuJing.clicked.connect(lambda: self.changeModelFile(None))  # 选择模型
        self.KaiShi.clicked.connect(self.start)  # 开始检测槽函数
        self.TingZhi.clicked.connect(self.stop)
        self.ShuRuFangShi.currentIndexChanged.connect(self.indexChanged)  # 输入方式切换
        self.BaoCunRiZhi.clicked.connect(lambda: self.saveToFile(self.BaoCunRiZhi))  # 保存日志
        self.BaoCunJieTu.clicked.connect(lambda: self.saveToFile(self.BaoCunJieTu))  # 保存截图
        self.LuZhiShiPin.clicked.connect(lambda: self.saveToFile(self.LuZhiShiPin))  # 保存视频
        self.XuanZeLeiBie.clicked.connect(lambda: self.changeClassFile(None))  # 选择类别
        self.LeiBie.textChanged.connect(self.displayClassNum)  # 显示类别个数
        self.LiuCheng.anchorClicked.connect(lambda x: os.popen(f'"{x.toLocalFile()}"'))  # 超链接打开本地文件
        self.XianShiZhenShu.stateChanged.connect(self.displayFps)  # 帧数显示
        self.DaYinJieGuo.clicked.connect(self.printResult)  # 打印检测结果
        self.BoFangJingBao.clicked.connect(self.printBoFang)  # 播放警报
        self.DaYinZuoBiao.clicked.connect(self.changeInputConfig)  # 是否返回坐标
        self.MaoKuang.clicked.connect(self.changeInputConfig)  # 是否画锚框
        self.ZhiXinDu.valueChanged.connect(self.changeInputConfig)  # 更改置信度
        self.IOU.valueChanged.connect(self.changeInputConfig)  # 更改IOU
        #self.ShuaXinLv.valueChanged.connect(self.changeInputConfig)  # 跳帧
        self.XuanZhuanTuXiang.currentIndexChanged.connect(self.changeInputConfig)  # 旋转
        self.FanZhuanTuXiang.currentIndexChanged.connect(self.changeInputConfig)  # 翻转
        self.MaoKuangYanSe.clicked.connect(self.changeBoxColor)  # 更改锚框颜色
        self.TiaoJieZiTi.clicked.connect(self.changeFont)  # 更改字体
        self.SuoDing.clicked.connect(self.lockBottom)  # 锁定切换 槽函数
        self.QingChu.clicked.connect(lambda: self.LiuCheng.clear())  # 清空控制台
        self.ChongZhi.clicked.connect(self.resetSource)  # 重置输入源


# ==================== 槽函数（按 UI() 中的绑定顺序排列） ====================
    # ↑ UI(): self.BaoCunLuJing.clicked —— 选择保存位置
    def changeOutputPath(self):  # 选择保存位置
        # 它会打开一个目录对话框让用户选择保存位置。然后，它会设置文本输入框的文本为保存位置的路径。
        file_path = QFileDialog.getExistingDirectory(self, "选择保存位置", self.BaoCun.text())
        if file_path:
            self.BaoCun.setText(file_path)

    # ↑ UI(): self.WenJianLuJing.clicked —— 选择媒体文件
    def changeMediaFile(self, path=None):  # 选择媒体文件
        # 如果没有提供路径，它会打开一个文件对话框让用户选择媒体文件。然后，它会设置输入源为媒体文件的路径。
        if path is None:
            path, _ = QFileDialog.getOpenFileName(self, "选择文件",
                                                  os.path.abspath(self.WenJian.text()),
                                                  '*.asf *.avi *.gif *.m4v *.mkv *.mov *.mp4 *.mpeg *.mpg *.ts *.wmv '
                                                  '*.bmp *.dng *.jpeg *.jpg *.mpo *.png *.tif *.tiff *.webp *.pfm')
        if path:
            self.setSource(path)

    # ↑ UI(): self.QuanZhongLuJing.clicked —— 选择模型
    def changeModelFile(self, path=None):  # 选择权重文件
        # 如果没有提供路径，它会打开一个文件对话框让用户选择模型文件。
        if path is None:
            path, _ = QFileDialog.getOpenFileName(self, "选择模型",
                                                  os.path.abspath(self.QuanZhong.text()),
                                                  '*.onnx')
        # 然后，它会设置文本输入框的文本为模型文件的路径。
        if path:
            self.QuanZhong.setText(path)
        # 最后，它会查找与模型文件同名的类别文件，如果存在，它会调用changeClassFile函数更改类别文件。
        class_txt_path = os.path.join(os.path.dirname(os.path.dirname(path)),
                                      ''.join(os.path.basename(path).split('.')[:-1]) + '.txt')
        if os.path.exists(class_txt_path):
            self.changeClassFile(path=class_txt_path)

    # ↑ UI(): self.KaiShi.clicked —— 开始检测
    def start(self):  # 启动检测线程
        # 如果检测线程已经在运行，它会打印一条消息并返回。如果模型文件或视频文件不存在，它会在日志中显示一条错误消息并返回。
        if self.dt.is_detecting:
            print('already running')
            return
        if not os.path.exists(self.QuanZhong.text()):
            self.displayLog(f'"{self.QuanZhong.text()}" 模型文件不存在', color='red')
            return
        if self.ShuRuFangShi.currentIndex() == 1 and not os.path.exists(self.WenJian.text()):  # 视频
            self.displayLog(f'"{self.WenJian.text()}" not exist', color='red')
            return
        if 'dataset' not in self.dt.__dict__.keys() and not self.setSource(self.source):
            return
        # 然后，它会初始化一个YOLOv5模型，并设置模型的配置，包括输入宽度、输入高度、置信度阈值、IOU阈值、是否绘制框、线宽、
        # 类名、框颜色、文本颜色和是否返回位置等。然后，它会初始化模型，并开始检测。最后，它会在状态栏上显示一条消息。
        self.dt.model = detect.YOLOv5()
        self.dt.model.initConfig(input_width=640,
                                 input_height=640,
                                 conf_thres=self.ZhiXinDu.value(),
                                 iou_thres=self.IOU.value(),
                                 draw_box=self.MaoKuang.isChecked(),
                                 thickness=2,
                                 class_names=self.LeiBie.text().split(','),
                                 box_color=self.box_color,
                                 txt_color=tuple(255 - x for x in self.box_color),
                                 with_pos=self.DaYinZuoBiao.isChecked(),
                                 )

        self.dt.model.initModel(self.QuanZhong.text(), t='onnxruntime')  # cv2.dnn or onnxruntime

        self.dt.startDetect()
        self.saveToFile(self.LuZhiShiPin)
        print('start detect')
        #self.statusBar().showMessage('start detect...', 5000)

    # ↑ UI(): self.TingZhi.clicked；__init__: dt.finished —— 双源槽
    def stop(self):  # 停止检测
        # 它首先停止任何正在进行的录制。
        self.stopRecord()
        # 如果检测线程正在运行，它会停止检测，并在状态栏上显示一条消息。
        if self.dt.is_detecting:
            self.dt.stopDetect()
            #self.statusBar().showMessage('stop detect', 5000)
            print('stop detect')
            return
        # 如果检测线程正在运行但没有进行检测，它会停止线程并等待线程结束。
        if self.dt.is_running:
            self.dt.stopThread()
            self.dt.wait()

    # ↑ UI(): self.ShuRuFangShi.currentIndexChanged —— 输入方式切换
    def indexChanged(self, index):  # 切换输入方式
        # indexChanged函数用于切换输入方式。它首先阻止dt对象发出任何信号，然后停止并等待当前的检测线程。
        # 然后，根据下拉列表的当前索引来设置输入源。输入源可以是摄像头、文件、全屏。最后，它允许dt对象再次发出信号。
        self.dt.blockSignals(True)
        self.dt.stopThread()
        self.dt.wait()
        if index == 0:  # webcam 0
            self.setSource('0')
        elif index == 1 and os.path.exists(self.WenJian.text()):  # file
            self.setSource(self.WenJian.text())
        elif index == 2:  # full screen 0
            self.setSource('screen')
        self.dt.blockSignals(False)

    # ↑ UI(): self.BaoCunRiZhi/BaoCunJieTu/LuZhiShiPin.clicked —— 一槽三源，参数区分按钮
    def saveToFile(self, index):  # 保存截图、视频、日志
        # 具体的保存内容取决于传入的index参数。如果index等于self.BaoCunJieTu，则保存截图；
        # 如果index等于self.BaoCunRiZhi，则保存日志；如果index等于self.LuZhiShiPin，
        # 则根据self.LuZhiShiPin.isChecked()的值来决定是否开始或停止录屏。
        os.makedirs(self.BaoCun.text(), exist_ok=True) # 创建一个目录，该目录的路径是self.BaoCun.text()返回的字符串
        head = datetime.now().strftime('%m-%d %H-%M-%S') # 获取当前的日期和时间，并将其格式化为字符串
        # 保存截图
        if index == self.BaoCunJieTu: # 如果self.BaoCunJieTu是True
            path = os.path.join(self.BaoCun.text(), f'ScreenShot_{head}.png')  # 创建一个路径，该路径指向一个.png文件
            if self.TuXiangShuChu.pixmap() is None:
                return
            self.TuXiangShuChu.pixmap().toImage().save(path) # 否则，将self.TuXiangShuChu.pixmap()转换为图像，并将其保存到path指向的文件中
            print(f'ScreenShot has been saved to <a href="file:///{path}">{path}</a>') # 打印一条消息，告诉用户截图已经被保存
        # 保存日志
        elif index == self.BaoCunRiZhi:
            path = os.path.join(self.BaoCun.text(), f'log_{head}.log')
            with open(path, 'w') as f:
                f.write(self.LiuCheng.toPlainText())
                print(f'Log has been saved to <a href="file:///{path}">{path}</a>')
        # 保存录屏视频
        elif index == self.LuZhiShiPin and self.LuZhiShiPin.isChecked() and self.dt.is_detecting:
            if self.dt.dataset.is_image:
                return
            self.save_video_path = os.path.join(self.BaoCun.text(), f'video_{head}.mp4')
            fourcc = cv2.VideoWriter_fourcc(*'mp4v')  # 创建一个视频编解码器
            fps = self.LuZhiZhenLv.value() # 获取录制视频的帧率
            width, height = self.dt.dataset.w, self.dt.dataset.h  # 获取录制视频的宽度和高度
            self.video_writer = cv2.VideoWriter(self.save_video_path, fourcc, fps, (width, height))  # 写入视频
            self.save_video = True
            print(f'begin recording...') # 打印一条消息，告诉用户开始录制视频
        elif index == self.LuZhiShiPin and not self.LuZhiShiPin.isChecked():
            self.stopRecord()

    # ↑ UI(): self.XuanZeLeiBie.clicked —— 选择类别
    def changeClassFile(self, path=None):  # 选择类别文件
        # 如果没有提供路径，它会打开一个文件对话框让用户选择类别文件。然后，它会设置文本编辑器的文本为类别文件的内容。
        if path is None:
            path, _ = QFileDialog.getOpenFileName(self, "选择文件",
                                                  os.path.abspath(self.class_file),
                                                  '*.txt')
        if path:
            self.class_file = path
            with open(self.class_file, 'r') as f:
                self.LeiBie.setText(f.read().replace('，', ',').replace('|', ',').replace('\n', ','))

    # ↑ UI(): self.LeiBie.textChanged —— 显示类别个数
    def displayClassNum(self):  # 显示类别数量
        # 它首先从文本编辑器中获取类别列表，然后创建一个集合以去除重复的类别，并且去除空字符串。最后，它将类别数量显示在标签上。
        #class_set = set(self.LeiBie.toPlainText().split(","))
        class_set = set(self.LeiBie.text().split(","))
        class_set.discard('')
        self.label_32.setText(f'类别({len(class_set)}):')

    # ↑ UI(): self.XianShiZhenShu.stateChanged —— 帧数显示开关
    def displayFps(self):  # 显示FPS。将检测对象的display_fps属性设置为复选框的选中状态。
        self.dt.display_fps = self.XianShiZhenShu.isChecked()

    # ↑ UI(): self.DaYinJieGuo.clicked —— 打印检测结果开关
    def printResult(self):  # 打印检测结果,用于设置是否打印检测结果。
        self.dt.print_result = self.DaYinJieGuo.isChecked()

    # ↑ UI(): self.BoFangJingBao.clicked —— 警报开关
    def printBoFang(self):  # 播放警报。
        setIsFlasg()

    # ↑ UI(): self.DaYinZuoBiao/MaoKuang.clicked、ZhiXinDu/IOU.valueChanged、旋转/翻转.currentIndexChanged —— 一槽六源，参数热更新
    def changeInputConfig(self):  # 更改输入配置
        # 如果检测模型不为空，它会更改模型的置信度阈值、IOU阈值、是否显示锚框和是否返回坐标。
        # 如果数据集存在，它还会更改数据集的翻转和旋转类型。
        if self.dt.model is not None:
            self.dt.model.conf_threshold = self.ZhiXinDu.value()  # 更改置信度
            self.dt.model.iou_threshold = self.IOU.value()  # 更改IOU
            self.dt.model.draw_box = self.MaoKuang.isChecked()  # 是否显示锚框
            self.dt.model.with_pos = self.DaYinZuoBiao.isChecked()  # 是否返回坐标
        if 'dataset' in self.dt.__dict__.keys() and self.dt.dataset is not None:
            self.dt.dataset.flip = self.flip_type[self.FanZhuanTuXiang.currentIndex()]
            self.dt.dataset.rotate = self.rotate_type[self.XuanZhuanTuXiang.currentIndex()]

    # ↑ UI(): self.MaoKuangYanSe.clicked —— 更改锚框颜色
    def changeBoxColor(self, color: tuple = None):  # 更改锚框颜色
        # 如果没有提供颜色，它会打开一个颜色对话框让用户选择颜色。选择的颜色将被应用到锚框和文本颜色。
        if not color:
            old_color = self.dt.model.box_color if self.dt.model else self.box_color
            new_color = QtWidgets.QColorDialog.getColor(QtGui.QColor(*old_color))
            if not new_color.isValid():
                return
            color = new_color.getRgb()[0:3]
        self.MaoKuangYanSe.setStyleSheet(f"color:rgb{color}")
        self.box_color = color
        if self.dt.model is None:
            return
        self.dt.model.box_color = self.box_color
        self.dt.model.txt_color = tuple(255 - x for x in self.box_color)

    # ↑ UI(): self.TiaoJieZiTi.clicked —— 更改字体
    def changeFont(self):
        new_font, ok = QtWidgets.QFontDialog.getFont(self.font, self, options=QtWidgets.QFontDialog.DontUseNativeDialog)
        if ok:
            self.font = new_font
            self.setFont(new_font)
            self.updateFontForChildren(new_font)  # 更新所有子控件的字体
            self.saveConfig()  # 保存配置

    # ↑ UI(): self.SuoDing.clicked —— 控制台锁定底部
    def lockBottom(self):  # 锁定底部切换
        # 它将滚动条的值设置为最大值（如果按钮被按下）或最大值减一（如果按钮没有被按下）。
        scrollbar = self.LiuCheng.verticalScrollBar()
        scrollbar.setValue(scrollbar.maximum() if self.SuoDing.isChecked() else scrollbar.maximum() - 1)

    # ↑ UI(): self.ChongZhi.clicked —— 重置输入源
    def resetSource(self):  # 重置输入源
        # 如果当前正在进行检测，它将直接返回。否则，它会根据下拉列表的当前索引更改输入源。
        # 这个函数可能用于在不同的输入源之间切换，例如从一个视频文件切换到另一个视频文件，
        # 或者从视频文件切换到摄像头输入。这个函数的具体行为取决于indexChanged函数的实现。
        # 这个函数会在用户想要更改输入源时被调用。
        if self.dt.is_detecting:
            return
        self.indexChanged(self.ShuRuFangShi.currentIndex())


# ==================== 槽函数（系统/跨线程信号目标，不在 UI() 中绑定） ====================
    # __init__: self.dt.img_sig（检测线程 → 主线程，AutoConnection 自动排队）
    def displayImg(self, img: numpy.ndarray):  # 显示图片到标签上。
        # 如果正在保存视频，它会将图像写入视频写入器。然后，它将图像数据设置为脚本API的图像数据。
        # 然后，它创建一个QImage对象，将图像的宽度和高度缩放到标签的宽度和高度之间的较小值，然后将缩放后的图像设置为标签的像素图。
        if self.save_video:
            self.video_writer.write(cv2.cvtColor(img, cv2.COLOR_RGB2BGR))
        # self.script_api.img_data = img
        img = QtGui.QImage(img.data, img.shape[1], img.shape[0], img.shape[1] * 3, QtGui.QImage.Format_RGB888)
        p = min(self.TuXiangShuChu.width() / img.width(), self.TuXiangShuChu.height() / img.height())
        pix = QtGui.QPixmap(img).scaled(int(img.width() * p), int(img.height() * p))
        self.TuXiangShuChu.setPixmap(pix)

    # app.py: StdOut.signalForText（print 劫持 → 控制台）
    def displayLog(self, text: str, color='black', plain_text=False):  # 输出控制台信息到LiuCheng
        # 首先创建一个带有当前时间的头部字符串。
        head_ = f"{datetime.now().strftime('%H:%M:%S.%f')} >> "
        # 然后，根据文本是否以’<'开始或是否为纯文本，它以不同的方式添加文本到文本浏览器。
        if text.startswith(('<',)) or plain_text:
            self.LiuCheng.setTextColor(QtGui.QColor('black'))
            self.LiuCheng.append(head_)
            self.LiuCheng.setTextColor(QtGui.QColor(color))
            self.LiuCheng.insertPlainText(text)
        else:
            text = f"{head_}<font color='{color}'>{text}"
            self.LiuCheng.append(text)
        # 自动切换锁定状态，根据滚动条的值是否大于或等于其最大值来设置复选按钮的选中状态，并根据复选按钮的选中状态来设置滚动条的值。
        scrollbar = self.LiuCheng.verticalScrollBar()
        self.SuoDing.setChecked(scrollbar.value() >= scrollbar.maximum())
        if self.SuoDing.isChecked():
            scrollbar.setValue(scrollbar.maximum())


# ==================== 内部辅助（不连任何信号） ====================
    def setSource(self, source, **kwargs) -> bool:  # 设置输入源。
        self.source = str(source) # 它首先将输入源转换为字符串
        # 然后尝试创建一个新的DataLoader实例，该实例使用输入源、帧跳过数、旋转类型作为参数。
        try:
            self.dt.dataset = detect.DataLoader(self.source,
                                                # frame_skip=self.ShuaXinLv.value(),
                                                flip=self.flip_type[self.FanZhuanTuXiang.currentIndex()],
                                                rotate=self.rotate_type[self.XuanZhuanTuXiang.currentIndex()],
                                                **kwargs)
        # 如果在创建DataLoader实例时发生异常，它会在标签上显示错误信息，并在日志中以红色显示错误信息，然后返回False。
        except Exception as e:
            self.TuXiangShuChu.setText(str(e))
            self.displayLog(str(e), color='red')
            return False
        # 否则，它会停止任何正在进行的录制，阻止下拉列表发出信号，然后根据输入源的类型设置下拉列表的当前索引。
        # 最后，它允许下拉列表再次发出信号，如果数据集是摄像头或屏幕，它会启动检测线程。
        self.stopRecord()
        self.ShuRuFangShi.blockSignals(True)
        index = (self.source == '0',
                 self.dt.dataset.is_image or self.dt.dataset.is_video,
                 # self.dt.dataset.is_url,
                 self.source.lower() == 'screen',
                 True).index(True)
        self.ShuRuFangShi.setCurrentIndex(index)
        self.ShuRuFangShi.blockSignals(False)
        # 如果数据集是图像或视频，它会设置文本输入框的文本为输入源，然后从输入源读取一帧图像，可能会翻转和旋转图像，然后显示图像。
        if self.dt.dataset.is_wabcam or self.dt.dataset.is_screen:
            self.dt.startThread()
        elif self.dt.dataset.is_image or self.dt.dataset.is_video:
            self.WenJian.setText(self.source)
            vc = cv2.VideoCapture(self.source)
            img = vc.read()[1]
            if self.FanZhuanTuXiang.currentIndex() != 0:
                img = cv2.flip(img, self.flip_type[self.FanZhuanTuXiang.currentIndex()])
            if self.XuanZhuanTuXiang.currentIndex() != 0:
                img = cv2.rotate(img, self.rotate_type[self.XuanZhuanTuXiang.currentIndex()])
            self.displayImg(cv2.cvtColor(img, cv2.COLOR_BGR2RGB))
            vc.release()
        # 最后，它返回一个布尔值，表示dt对象是否有一个dataset属性。
        return 'dataset' in self.dt.__dict__.keys()

    def stopRecord(self):  # 停止录制，如果当前没有录制视频，它将直接返回。否则，它会停止录制并释放视频写入器。
        if not self.save_video:
            return
        self.save_video = False
        self.video_writer.release()
        print(f'Video has been saved to <a href="file:///{self.save_video_path}">{self.save_video_path}</a>')

    def loadConfig(self):  # 从配置文件`config.cfg`中加载配置。
        # 这些配置包括帧跳过数、翻转类型、旋转类型、输入源、模型路径、类别路径、是否显示帧数、置信度阈值、
        # IOU阈值、是否显示框、框颜色、是否打印结果、是否返回位置、是否记录视频、记录帧数、输出路径、脚本路径、脚本状态和检测状态等。
        # 这些配置被用来初始化各种参数和设置。
        cfg = general.cfg('config.cfg')
        #self.ShuaXinLv.setValue(cfg.search('root', 'frame_skip', default_value=-1, return_type=int))
        self.FanZhuanTuXiang.setCurrentIndex(cfg.search('root', 'flip', default_value=0, return_type=int))
        self.XuanZhuanTuXiang.setCurrentIndex(cfg.search('root', 'rotate', default_value=0, return_type=int))
        self.setSource(cfg.search('root', 'input_source', default_value=0))
        self.QuanZhong.setText(cfg.search('root', 'model_path', os.path.join('need', 'models', 'm0.9.onnx')))
        self.class_file = cfg.search('root', 'class_path', os.path.join('need', 'm0.9.txt'))
        if os.path.exists(self.class_file):
            self.LeiBie.setText(open(self.class_file, 'r').read().replace('\n', ','))  # 初始化类别
        self.XianShiZhenShu.setChecked(cfg.search('root', 'display_fps', default_value=True, return_type=bool))
        self.ZhiXinDu.setValue(cfg.search('root', 'conf_thres', default_value=0.35, return_type=float))
        self.IOU.setValue(cfg.search('root', 'iou_thres', default_value=0.35, return_type=float))
        self.MaoKuang.setChecked(cfg.search('root', 'display_box', default_value=True, return_type=bool))
        self.changeBoxColor(eval(cfg.search('root', 'box_color', default_value='(255,0,0)')))
        font_config = cfg.search('root', 'font', default_value='("Arial", 12)')
        font_name, font_size = eval(font_config)
        self.font = QtGui.QFont(font_name, font_size)
        self.setFont(self.font)
        self.updateFontForChildren(self.font)  # 更新所有子控件的字体
        self.DaYinJieGuo.setChecked(cfg.search('root', 'print_result', default_value=True, return_type=bool))
        self.DaYinZuoBiao.setChecked(cfg.search('root', 'with_pos', default_value=False, return_type=bool))
        self.LuZhiShiPin.setChecked(cfg.search('root', 'record_video', default_value=False, return_type=bool))
        self.LuZhiZhenLv.setValue(cfg.search('root', 'record_fps', default_value=15, return_type=int))
        self.BaoCun.setText(cfg.search('root', 'out_path', default_value=os.path.join(os.getcwd(), 'out')))
        if cfg.search('root', 'detect_status', default_value=False, return_type=bool):
            self.start()

    def saveConfig(self):  # 保存配置,将当前的配置保存到`config.cfg`文件中。
        # 这些配置包括检测状态、输入源、帧跳过数、翻转类型、旋转类型、模型路径、类别路径、是否显示帧数、置信度阈值、
        # IOU阈值、是否显示框、框颜色、是否打印结果、是否返回位置、是否记录视频、记录帧数等。
        # 这些配置在下次启动程序时可以被加载，以恢复上次的设置。这样可以提高用户体验，因为用户不需要每次启动程序时都重新设置这些参数。
        # 这也是一种常见的设计模式，被称为“持久化配置”。
        with general.cfg('config.cfg') as cfg:
            cfg.set('root', 'detect_status', self.dt.is_detecting)
            cfg.set('root', 'input_source', self.source)
            #cfg.set('root', 'frame_skip', self.ShuaXinLv.value())
            cfg.set('root', 'flip', self.FanZhuanTuXiang.currentIndex())
            cfg.set('root', 'rotate', self.XuanZhuanTuXiang.currentIndex())
            cfg.set('root', 'model_path', self.QuanZhong.text())
            cfg.set('root', 'class_path', self.class_file)
            cfg.set('root', 'display_fps', self.XianShiZhenShu.isChecked())
            cfg.set('root', 'conf_thres', self.ZhiXinDu.value())
            cfg.set('root', 'iou_thres', self.IOU.value())
            cfg.set('root', 'display_box', self.MaoKuang.isChecked())
            cfg.set('root', 'box_color', self.box_color)
            cfg.set('root', 'font', f'("{self.font.family()}", {self.font.pointSize()})')
            cfg.set('root', 'print_result', self.DaYinJieGuo.isChecked())
            cfg.set('root', 'with_pos', self.DaYinZuoBiao.isChecked())
            cfg.set('root', 'record_video', self.LuZhiShiPin.isChecked())
            cfg.set('root', 'record_fps', self.LuZhiZhenLv.value())
            cfg.set('root', 'out_path', self.BaoCun.text())

    def updateFontForChildren(self, font):
        for widget in self.findChildren(QtWidgets.QWidget):
            widget.setFont(font)


# ==================== Qt事件 ====================
    def eventFilter(self, objwatched, event):  # 重写事件过滤
        # 它首先检查观察对象和事件类型。
        eventType = event.type()
        # 关闭窗口事件
        # 这段代码是对窗口关闭事件和焦点事件的处理。如果事件类型是窗口关闭事件(QtCore.QEvent.Close)，并且检测线程正在运行，
        # 那么会弹出一个消息框询问用户是否停止并关闭。如果用户选择"Yes"，那么会停止检测线程；
        # 如果用户选择"No"，那么会忽略这个关闭事件并返回True，这样窗口就不会关闭。
        # 无论用户选择什么，都会保存配置，并将标准输出和错误输出重定向回原来的地方。
        if eventType == QtCore.QEvent.Close:
            if self.dt.is_detecting:
                msgbox = QMessageBox.question(self,
                                              self.windowTitle(),
                                              '正在运行\n是否停止并关闭?',
                                              QMessageBox.Yes | QMessageBox.Ignore | QMessageBox.No,
                                              QMessageBox.Yes)
                if msgbox == QMessageBox.Yes:
                    self.stop()
                elif msgbox == QMessageBox.No:
                    event.ignore()
                    return True
            self.saveConfig()
            sys.stdout = sys.__stdout__
            sys.stderr = sys.__stderr__
        return super().eventFilter(objwatched, event)
        # 最后，这个函数会调用父类的eventFilter方法处理其他类型的事件。
