# import logging  # 导入logging模块，用于记录日志
# import hashlib  # 导入hashlib模块，用于哈希操作
# import pymysql
# from PyQt5 import QtWidgets, QtCore
# from PyQt5 import QtCore, QtWidgets  # 从PyQt5库导入QtCore, QtGui, QtWidgets模块，用于创建图形用户界面(GUI)
# from PyQt5.QtWidgets import QMessageBox
# from cushy_storage import CushyDict  # 从cushy_storage模块导入CushyDict类，可能用于数据存储
#
# from UI.DengLu import Ui_DengLu_MainWindow  # 从pages.login模块导入Ui_MainWindow类，这是一个用于创建登录窗口的用户界面类
#
#
# class LoginController(QtWidgets.QMainWindow, Ui_DengLu_MainWindow):  # 定义LoginController类，它继承自QtWidgets.QMainWindow和Ui_MainWindow
#     to_register_page_signal = QtCore.pyqtSignal()  # 定义一个信号，用于在需要跳转到注册页面时发出
#     to_home_page_signal = QtCore.pyqtSignal()  # 定义一个信号，用于在需要跳转到主页时发出
#
#     def __init__(self):  # 定义构造函数
#         super().__init__()  # 调用父类的构造函数
#         self.setupUi(self)  # 调用setupUi方法，设置用户界面
#         self.init_attr()  # 调用init_attr方法，初始化属性
#         self.init_slot()  # 调用init_slot方法，初始化槽
#
#         self.cache = CushyDict("./cache")  # 创建一个CushyDict对象，用于缓存数据
#         self.logger = logging.getLogger(__name__)  # 创建一个logger对象，用于记录日志
#
#     def init_attr(self):  # 定义init_attr方法，用于初始化属性
#         #self.setWindowTitle("Login Page")  # 设置窗口的标题为"Login Page"
#         self.ShuRuYongHuMing.setPlaceholderText("请输入帐号")  # 设置帐号输入框的占位符文本
#         self.ShuRuMiMa.setPlaceholderText("请输入密码")  # 设置密码输入框的占位符文本
#
#     def init_slot(self):  # 定义init_slot方法，用于初始化槽
#         self.DengLu.clicked.connect(self.login)  # 当登录按钮被点击时，调用login方法
#         self.ZhuCeZhangHao.clicked.connect(self.to_register_page)  # 当注册按钮被点击时，调用to_register_page方法
#
#     # def login(self):  # 定义login方法，用于处理登录操作
#     #     account = self.ShuRuYongHuMing.text()  # 获取帐号输入框的文本
#     #     password = self.ShuRuMiMa.text()  # 获取密码输入框的文本
#     #     self.logger.debug(f"[user] account: {account} password: {password}")  # 记录日志
#     #     self._validate_user(account, password)  # 调用_validate_user方法，验证用户
#     def create_connection(self):
#         return pymysql.connect(host='localhost',
#                                user='123',  # 替换为您的数据库用户名
#                                password='123456',  # 替换为您的数据库密码
#                                db='firesmokeusers',  # 您的数据库名
#                                charset='utf8mb4')
#
#     def login(self):
#         account = self.ShuRuYongHuMing.text()
#         password = self.ShuRuMiMa.text()
#
#         # 使用MD5加密用户输入的密码
#         m = hashlib.md5()
#         m.update(password.encode('utf-8'))
#         encrypted_password = m.hexdigest()
#
#         # 在try块之前初始化conn为None
#         conn = None
#         try:
#             conn = self.create_connection()
#             with conn.cursor() as cursor:
#                 sql = "SELECT password FROM users WHERE username=%s"
#                 cursor.execute(sql, (account,))
#                 result = cursor.fetchone()
#                 if result and result[0] == encrypted_password:  # 比较加密后的密码
#                     QMessageBox.about(self, "提示", "登陆成功")
#                     self.to_home_page_signal.emit()
#                 else:
#                     QMessageBox.about(self, "提示", "帐号或密码错误")
#         except pymysql.MySQLError as e:
#             self.logger.error(f"Database error: {e}")
#             QMessageBox.about(self, "提示", "登录失败，数据库错误")
#         finally:
#             # 检查conn是否不为None再尝试关闭它
#             if conn is not None:
#                 conn.close()
#
#     def _validate_user(self, account: str, password: str):  # 定义_validate_user方法，用于验证用户
#         if account in self.cache:  # 如果帐号在缓存中存在
#             m = hashlib.md5()  # 创建一个md5哈希对象
#             m.update(password.encode('utf-8'))  # 更新哈希对象，输入为密码的utf-8编码
#             enc_pwd = m.hexdigest()  # 获取哈希的十六进制字符串表示
#
#             if self.cache[account] == enc_pwd:  # 如果缓存中的密码与输入的密码匹配
#                 self.logger.debug(enc_pwd)  # 记录日志
#                 QMessageBox.about(self, "提示", "登陆成功")  # 显示一个消息框，提示登录成功
#                 self.to_home_page_signal.emit()  # 发出to_home_page_signal信号
#             else:  # 如果缓存中的密码与输入的密码不匹配
#                 QMessageBox.about(self, "提示", "密码错误")  # 显示一个消息框，提示密码错误
#         else:  # 如果帐号在缓存中不存在
#             QMessageBox.about(self, "提示", "帐号不存在，请注册")  # 显示一个消息框，提示帐号不存在
#
#     def to_register_page(self):  # 定义to_register_page方法，用于跳转到注册页面
#         self.to_register_page_signal.emit()  # 发出to_register_page_signal信号
import logging  # 导入logging模块，用于记录日志
import hashlib  # 导入hashlib模块，用于哈希操作

from PyQt5 import QtCore, QtGui, QtWidgets  # 从PyQt5库导入QtCore, QtGui, QtWidgets模块，用于创建图形用户界面(GUI)
from PyQt5.QtWidgets import QMessageBox
from cushy_storage import CushyDict  # 从cushy_storage模块导入CushyDict类，可能用于数据存储

from UI.DengLu import Ui_DengLu_MainWindow  # 从pages.login模块导入Ui_MainWindow类，这是一个用于创建登录窗口的用户界面类


class LoginController(QtWidgets.QMainWindow, Ui_DengLu_MainWindow):  # 定义LoginController类，它继承自QtWidgets.QMainWindow和Ui_MainWindow
    to_register_page_signal = QtCore.pyqtSignal()  # 定义一个信号，用于在需要跳转到注册页面时发出
    to_home_page_signal = QtCore.pyqtSignal()  # 定义一个信号，用于在需要跳转到主页时发出

    def __init__(self):  # 定义构造函数
        super().__init__()  # 调用父类的构造函数
        self.setupUi(self)  # 调用setupUi方法，设置用户界面
        self.init_attr()  # 调用init_attr方法，初始化属性
        self.init_slot()  # 调用init_slot方法，初始化槽

        self.cache = CushyDict("./cache")  # 创建一个CushyDict对象，用于缓存数据
        self.logger = logging.getLogger(__name__)  # 创建一个logger对象，用于记录日志

    def init_attr(self):  # 定义init_attr方法，用于初始化属性
        #self.setWindowTitle("Login Page")  # 设置窗口的标题为"Login Page"
        self.ShuRuYongHuMing.setPlaceholderText("请输入帐号")  # 设置帐号输入框的占位符文本
        self.ShuRuMiMa.setPlaceholderText("请输入密码")  # 设置密码输入框的占位符文本

    def init_slot(self):  # 定义init_slot方法，用于初始化槽
        self.DengLu.clicked.connect(self.login)  # 当登录按钮被点击时，调用login方法
        self.ZhuCeZhangHao.clicked.connect(self.to_register_page)  # 当注册按钮被点击时，调用to_register_page方法

    def login(self):  # 定义login方法，用于处理登录操作
        account = self.ShuRuYongHuMing.text()  # 获取帐号输入框的文本
        password = self.ShuRuMiMa.text()  # 获取密码输入框的文本
        self.logger.debug(f"[user] account: {account} password: {password}")  # 记录日志
        self._validate_user(account, password)  # 调用_validate_user方法，验证用户

    def _validate_user(self, account: str, password: str):  # 定义_validate_user方法，用于验证用户
        if account in self.cache:  # 如果帐号在缓存中存在
            m = hashlib.md5()  # 创建一个md5哈希对象
            m.update(password.encode('utf-8'))  # 更新哈希对象，输入为密码的utf-8编码
            enc_pwd = m.hexdigest()  # 获取哈希的十六进制字符串表示

            if self.cache[account] == enc_pwd:  # 如果缓存中的密码与输入的密码匹配
                self.logger.debug(enc_pwd)  # 记录日志
                QMessageBox.about(self, "提示", "登陆成功")  # 显示一个消息框，提示登录成功
                self.to_home_page_signal.emit()  # 发出to_home_page_signal信号
            else:  # 如果缓存中的密码与输入的密码不匹配
                QMessageBox.about(self, "提示", "密码错误")  # 显示一个消息框，提示密码错误
        else:  # 如果帐号在缓存中不存在
            QMessageBox.about(self, "提示", "帐号不存在，请注册")  # 显示一个消息框，提示帐号不存在

    def to_register_page(self):  # 定义to_register_page方法，用于跳转到注册页面
            self.to_register_page_signal.emit()  # 发出to_register_page_signal信号