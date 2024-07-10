# import logging  # 导入logging模块，用于记录日志
# import hashlib  # 导入hashlib模块，用于哈希操作
# from PyQt5 import QtWidgets  # 从PyQt5库导入QtCore, QtGui, QtWidgets模块，用于创建图形用户界面(GUI)
# from PyQt5.QtWidgets import QMessageBox
# from cushy_storage import CushyDict  # 从cushy_storage模块导入CushyDict类，可能用于数据存储
# import pymysql
# from UI.ZhuCe import Ui_ZhuCe_MainWindow  # 从pages.register模块导入Ui_MainWindow类，这是一个用于创建注册窗口的用户界面类
#
#
# class RegisterController(QtWidgets.QMainWindow, Ui_ZhuCe_MainWindow):  # 定义RegisterController类，它继承自QtWidgets.QMainWindow和Ui_MainWindow
#
#     def __init__(self):  # 定义构造函数
#         super().__init__()  # 调用父类的构造函数
#         self.setupUi(self)  # 调用setupUi方法，设置用户界面
#         self.init_attr()  # 调用init_attr方法，初始化属性
#         self.init_slot()  # 调用init_slot方法，初始化槽
#
#         self.cache = CushyDict('./cache')  # 创建一个CushyDict对象，用于缓存数据
#         self.logger = logging.getLogger(__name__)  # 创建一个logger对象，用于记录日志
#
#     def init_attr(self):  # 定义init_attr方法，用于初始化属性
#         self.setWindowTitle("Register Page")  # 设置窗口的标题为"Register Page"
#
#     def init_slot(self):  # 定义init_slot方法，用于初始化槽
#         self.ZhuCe.clicked.connect(self.register)  # 当注册按钮被点击时，调用register方法
#
#     # def register(self):  # 定义register方法，用于处理注册操作
#     #     account = self.ShuRuZhangHao.text()  # 获取帐号输入框的文本
#     #     password = self.SheZhiMiMa.text()  # 获取密码输入框的文本
#     #     self.logger.debug(f"[user] account: {account} password: {password}")  # 记录日志
#     #
#     #     # 创建md5对象
#     #     m = hashlib.md5()
#     #     # 更新md5加密内容
#     #     m.update(password.encode('utf-8'))
#     #     # 获取加密后的字符串，以16进制输出
#     #     result = m.hexdigest()
#     #
#     #     self.logger.debug(result)  # 记录日志
#     #     self.cache[account] = result  # 将帐号和加密后的密码存入缓存
#     #     QMessageBox.about(self, "提示", "注册成功")  # 显示一个消息框，提示注册成功
#     #     self.close()  # 关闭窗口
#     def create_connection(self):
#         return pymysql.connect(host='localhost',
#                                user='123',  # 替换为您的数据库用户名
#                                password='123456',  # 替换为您的数据库密码
#                                db='firesmokeusers',  # 您的数据库名
#                                charset='utf8mb4')
#
#     def register(self):
#         account = self.ShuRuZhangHao.text()
#         password = self.SheZhiMiMa.text()
#
#         # 使用MD5加密密码
#         m = hashlib.md5()
#         m.update(password.encode('utf-8'))
#         encrypted_password = m.hexdigest()
#
#         conn = None  # 在try块之前初始化conn
#         try:
#             conn = self.create_connection()
#             with conn.cursor() as cursor:
#                 sql = "INSERT INTO users (username, password) VALUES (%s, %s)"
#                 cursor.execute(sql, (account, encrypted_password))
#                 conn.commit()
#             QMessageBox.about(self, "提示", "注册成功")
#         except pymysql.MySQLError as e:
#             self.logger.error(f"Database error: {e}")
#             QMessageBox.about(self, "提示", "注册失败，数据库错误")
#         finally:
#             if conn:  # 现在conn已经被定义
#                 conn.close()
#         self.close()
import logging  # 导入logging模块，用于记录日志
import re
import hashlib  # 导入hashlib模块，用于哈希操作
from PyQt5 import QtCore, QtWidgets  # 从PyQt5库导入QtCore, QtGui, QtWidgets模块，用于创建图形用户界面(GUI)
from PyQt5.QtWidgets import QMessageBox
from cushy_storage import CushyDict  # 从cushy_storage模块导入CushyDict类，可能用于数据存储

from UI.ZhuCe import Ui_ZhuCe_MainWindow  # 从pages.register模块导入Ui_MainWindow类，这是一个用于创建注册窗口的用户界面类


class RegisterController(QtWidgets.QMainWindow, Ui_ZhuCe_MainWindow):  # 定义RegisterController类，它继承自QtWidgets.QMainWindow和Ui_MainWindow
    to_Login_page_signal = QtCore.pyqtSignal()  # 定义一个信号，用于在需要跳转到登录页面时发出

    def __init__(self):  # 定义构造函数
        super().__init__()  # 调用父类的构造函数
        self.setupUi(self)  # 调用setupUi方法，设置用户界面
        self.init_attr()  # 调用init_attr方法，初始化属性
        self.init_slot()  # 调用init_slot方法，初始化槽

        self.cache = CushyDict('./cache')  # 创建一个CushyDict对象，用于缓存数据
        self.logger = logging.getLogger(__name__)  # 创建一个logger对象，用于记录日志

    def init_attr(self):  # 定义init_attr方法，用于初始化属性
        self.setWindowTitle("Register Page")  # 设置窗口的标题为"Register Page"

    def init_slot(self):  # 定义init_slot方法，用于初始化槽
        self.ZhuCe.clicked.connect(self.register)  # 当注册按钮被点击时，调用register方法
        self.FanHuiDengLu.clicked.connect(self.to_Login_page)  # 当返回登录按钮被点击时，调用to_Login_page方法

    def to_Login_page(self):  # 定义to_Login_page方法，用于跳转到登录页面
            self.to_Login_page_signal.emit()  # 发出to_Login_page_signal信号

    def register(self):
        account = self.ShuRuZhangHao.text()  # 获取帐号输入框的文本
        password = self.SheZhiMiMa.text()  # 获取密码输入框的文本
        password_2 = self.QueRenMiMa.text()  # 获取确认密码输入框的文本

        # 使用正则表达式验证用户名和密码
        # 用户名必须以英文字符开头，最小3位，最大16位
        account_pattern = re.compile(r'^[a-zA-Z][a-zA-Z0-9]{2,15}$')
        # 密码最小3位最大8位，只包含数字和英文字符
        password_pattern = re.compile(r'^[a-zA-Z0-9]{3,8}$')


        if not account_pattern.match(account):
            QMessageBox.warning(self, "错误", "用户名必须以英文字母开头，且长度在3到16位之间，只包含数字和英文字母")
            return
        if not password_pattern.match(password):
            QMessageBox.warning(self, "错误", "密码长度必须在3到8位之间，只包含数字和英文字母")
            return
        if not password==password_2:
            QMessageBox.warning(self, "错误", "两次输入密码不一致")
            return
        if account in self.cache:  # 如果帐号在缓存中存在
            QMessageBox.warning(self, "错误", "用户已存在,用户名不区分大小写")
            return

        self.logger.debug(f"[user] account: {account} password: {password}")  # 记录日志

        # 创建md5对象，加密密码
        m = hashlib.md5()
        m.update(password.encode('utf-8'))
        result = m.hexdigest()

        self.logger.debug(result)  # 记录日志
        self.cache[account] = result  # 将帐号和加密后的密码存入缓存
        QMessageBox.about(self, "提示", "注册成功")  # 显示一个消息框，提示注册成功
        self.close()  # 关闭窗口