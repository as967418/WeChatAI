from PySide6.QtWidgets import (QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, 
                             QPushButton, QListWidget, QLabel, QSystemTrayIcon,
                             QMenu, QMessageBox, QApplication, QInputDialog, QLineEdit)
from PySide6.QtCore import Qt, QPoint, QTimer
from PySide6.QtGui import QIcon, QAction, QColor, QPalette, QFont,QIcon
import asyncio
import sys
import os
from .settings_dialog import SettingsDialog
import resources_rc

class MacStyleButton(QPushButton):
    def __init__(self, text='', button_type='primary', parent=None):
        super().__init__(text, parent)
        self.setMinimumHeight(32)
        self.setFont(QFont('SF Pro Display', 12))
        self.button_type = button_type
        self.update_style()

    def update_style(self):
        if self.button_type == 'primary':
            self.setStyleSheet("""
                QPushButton {
                    background-color: #007AFF;
                    color: white;
                    border: none;
                    border-radius: 6px;
                    padding: 5px 15px;
                }
                QPushButton:hover {
                    background-color: #0069D9;
                }
                QPushButton:pressed {
                    background-color: #0051A8;
                }
                QPushButton:disabled {
                    background-color: #B3D7FF;
                }
            """)
        elif self.button_type == 'stop':
            self.setStyleSheet("""
                QPushButton {
                    background-color: #FF3B30;
                    color: white;
                    border: none;
                    border-radius: 6px;
                    padding: 5px 15px;
                }
                QPushButton:hover {
                    background-color: #DC3545;
                }
                QPushButton:pressed {
                    background-color: #C82333;
                }
                QPushButton:disabled {
                    background-color: #FFC1C1;
                }
            """)
        elif self.button_type == 'secondary':
            self.setStyleSheet("""
                QPushButton {
                    background-color: #E5E5EA;
                    color: #1D1D1F;
                    border: none;
                    border-radius: 6px;
                    padding: 5px 15px;
                }
                QPushButton:hover {
                    background-color: #D1D1D6;
                }
                QPushButton:pressed {
                    background-color: #C7C7CC;
                }
                QPushButton:disabled {
                    background-color: #F2F2F7;
                }
            """)

    def set_type(self, button_type):
        self.button_type = button_type
        self.update_style()

class MainWindow(QMainWindow):
    def __init__(self, config_manager, chat_manager, db_manager, app):
        super().__init__()
        self.config = config_manager
        self.chat = chat_manager
        self.db = db_manager
        self.app = app  # 保存应用程序实例
        self.running = False
        self.messages = []  # 存储消息记录
        self.setup_ui()
        self.load_window_settings()
        self.load_groups()  # 加载保存的群组
        self.load_trigger_word()  # 加载触发词
        self.setup_tray()
        self.apply_mac_style()
        self.setWindowIcon(QIcon(":bot.ico"))  # 设置任务栏图标


    def apply_mac_style(self):
        """应用类似macOS的样式"""
        self.setStyleSheet("""
            QMainWindow {
                background-color: #F5F5F7;
            }
            QWidget {
                font-family: 'SF Pro Display';
            }
            QLabel {
                color: #1D1D1F;
                font-size: 13px;
            }
            QListWidget {
                background-color: white;
                border: 1px solid #D2D2D7;
                border-radius: 8px;
                padding: 5px;
            }
            QListWidget::item {
                height: 30px;
                border-radius: 4px;
                padding: 5px;
            }
            QListWidget::item:selected {
                background-color: #007AFF;
                color: white;
            }
        """)

    def setup_ui(self):
        """设置UI界面"""
        self.setWindowTitle("微信AI助手")
        self.setWindowFlags(Qt.WindowStaysOnTopHint)
        self.setAttribute(Qt.WA_TranslucentBackground, False)
        self.resize(320, 480)

        # 创建主容器
        main_widget = QWidget()
        main_widget.setObjectName("mainWidget")
        main_widget.setStyleSheet("""
            #mainWidget {
                background-color: white;
                border: 1px solid #D2D2D7;
            }
        """)
        self.setCentralWidget(main_widget)
        layout = QVBoxLayout(main_widget)
        layout.setContentsMargins(15, 15, 15, 15)
        layout.setSpacing(10)

        # 状态和触发词区域
        status_widget = QWidget()
        status_layout = QVBoxLayout(status_widget)  # 改为垂直布局
        status_layout.setContentsMargins(0, 0, 0, 0)
        status_layout.setSpacing(5)  # 设置垂直间距
        
        # 状态显示
        self.status_label = QLabel("当前状态: 未运行")
        self.status_label.setStyleSheet("color: #86868B;")
        status_layout.addWidget(self.status_label)
        
        # 触发词显示和编辑（新的一行）
        trigger_widget = QWidget()
        trigger_layout = QHBoxLayout(trigger_widget)
        trigger_layout.setContentsMargins(0, 0, 0, 0)
        
        trigger_label = QLabel("触发词:")
        trigger_label.setStyleSheet("color: #86868B;")
        self.trigger_edit = QLineEdit()
        self.trigger_edit.setText("AI")  # 设置默认触发词
        self.trigger_edit.setMaximumWidth(120)  # 稍微增加宽度
        self.trigger_edit.setStyleSheet("""
            QLineEdit {
                background-color: #F5F5F7;
                border: 1px solid #D2D2D7;
                border-radius: 4px;
                padding: 2px 5px;
                color: #007AFF;
                font-size: 12px;
                height: 24px;
            }
        """)
        self.trigger_edit.textChanged.connect(self.update_trigger_word)
        
        trigger_layout.addWidget(trigger_label)
        trigger_layout.addWidget(self.trigger_edit)
        trigger_layout.addStretch()  # 添加弹性空间
        
        status_layout.addWidget(trigger_widget)
        layout.addWidget(status_widget)

        # 群组管理区域
        group_header = QWidget()
        group_layout = QHBoxLayout(group_header)
        group_layout.setContentsMargins(0, 0, 0, 0)
        
        list_label = QLabel("监听的群组")
        list_label.setFont(QFont('SF Pro Display', 14, QFont.Bold))
        group_layout.addWidget(list_label)
        group_layout.addStretch()
        
        # 添加和删除群组的按钮
        add_group_btn = QPushButton("+")
        add_group_btn.setFixedSize(24, 24)
        add_group_btn.setStyleSheet("""
            QPushButton {
                background-color: #007AFF;
                color: white;
                border-radius: 12px;
                font-weight: bold;
                font-size: 16px;
            }
            QPushButton:hover {
                background-color: #0069D9;
            }
        """)
        add_group_btn.clicked.connect(lambda: self.app.run_coroutine(self.add_group()))
        
        remove_group_btn = QPushButton("-")
        remove_group_btn.setFixedSize(24, 24)
        remove_group_btn.setStyleSheet("""
            QPushButton {
                background-color: #FF3B30;
                color: white;
                border-radius: 12px;
                font-weight: bold;
                font-size: 16px;
            }
            QPushButton:hover {
                background-color: #DC3545;
            }
        """)
        remove_group_btn.clicked.connect(self.remove_group)
        
        group_layout.addWidget(add_group_btn)
        group_layout.addWidget(remove_group_btn)
        layout.addWidget(group_header)
        
        self.group_list = QListWidget()
        self.group_list.setMinimumHeight(120)  # 减小高度以适应新增的消息列表
        self.update_group_list()
        layout.addWidget(self.group_list)

        # 添加消息记录显示区域
        message_label = QLabel("消息记录")
        message_label.setFont(QFont('SF Pro Display', 14, QFont.Bold))
        layout.addWidget(message_label)
        
        self.message_list = QListWidget()
        self.message_list.setMinimumHeight(150)
        self.message_list.setStyleSheet("""
            QListWidget {
                background-color: white;
                border: 1px solid #D2D2D7;
                border-radius: 8px;
                padding: 5px;
            }
            QListWidget::item {
                border-bottom: 1px solid #E5E5EA;
                padding: 8px;
            }
        """)
        layout.addWidget(self.message_list)

        # 按钮区域
        button_layout = QHBoxLayout()
        button_layout.setSpacing(10)
        
        self.start_btn = MacStyleButton("开始监听", "primary")
        self.start_btn.clicked.connect(lambda: self.app.run_coroutine(self.toggle_service()))
        
        settings_btn = MacStyleButton("设置", "secondary")
        settings_btn.clicked.connect(self.show_settings)
        
        button_layout.addWidget(self.start_btn)
        button_layout.addWidget(settings_btn)
        layout.addLayout(button_layout)

        # 创建一个 QLabel 并设置其文本为 HTML 格式，包含一个可点击的链接
        self.about_label = QLabel(
            '<p><a href="https://www.allfather.top">愿代码流畅无阻，愿调试轻松自如</a></p>',
            self
        )
        # self.about_label.setStyleSheet("background: lightblue")
        self.about_label.setAlignment(Qt.AlignBottom | Qt.AlignRight)
        self.about_label.setOpenExternalLinks(True)  # 允许 QLabel 中的链接被点击跳转
        # 将 QLabel 添加到布局中
        layout.addWidget(self.about_label)

        # 添加加载指示器
        self.loading_label = QLabel()
        self.loading_label.setStyleSheet("""
            QLabel {
                color: #007AFF;
                font-size: 12px;
                font-style: italic;
            }
        """)
        self.loading_label.hide()
        layout.addWidget(self.loading_label)

    def setup_tray(self):
        """设置系统托盘"""
        # 移除系统托盘功能
        pass

    def load_window_settings(self):
        """加载窗口设置"""
        settings = self.config.get_window_settings()
        if settings.get("position"):
            self.move(settings["position"]["x"], settings["position"]["y"])
        if settings.get("always_on_top"):
            self.setWindowFlags(self.windowFlags() | Qt.WindowStaysOnTopHint)

    def save_window_settings(self):
        """保存窗口设置"""
        pos = self.pos()
        settings = {
            "position": {"x": pos.x(), "y": pos.y()},
            "always_on_top": bool(self.windowFlags() & Qt.WindowStaysOnTopHint)
        }
        self.config.set_window_settings(settings)

    def load_groups(self):
        """加载保存的群组列表"""
        try:
            # 从数据库或配置中加载群组
            groups = self.chat.get_groups()
            # 更新UI显示
            self.update_group_list()
            # 如果有群组，更新状态显示
            if groups:
                self.status_label.setText("当前状态: 就绪")
        except Exception as e:
            self.status_label.setText("当前状态: 加载群组失败")

    def update_group_list(self):
        """更新群组列表"""
        self.group_list.clear()
        groups = self.chat.get_groups()
        for group in groups:
            self.group_list.addItem(group)

    def load_trigger_word(self):
        """加载触发词"""
        trigger_word = self.config.get_trigger_word()
        self.trigger_edit.setText(trigger_word)
        self.status_label.setText(f"当前状态: 未运行 (触发词: @{trigger_word})")

    def update_trigger_word(self):
        """更新触发词"""
        trigger_word = self.trigger_edit.text().strip()
        if trigger_word:
            self.config.set_trigger_word(trigger_word)
            if not self.running:
                self.status_label.setText(f"当前状态: 未运行 (触发词: @{trigger_word})")
            else:
                self.status_label.setText(f"当前状态: 运行中 (触发词: @{trigger_word})")

    async def add_group(self):
        """异步添加群组"""
        dialog = QInputDialog(self)
        dialog.setWindowTitle("添加群组")
        dialog.setLabelText("请输入要监听的群组名称:")
        dialog.setStyleSheet("""
            QInputDialog {
                background-color: #F5F5F7;
            }
            QLabel {
                color: #1D1D1F;
                font-size: 13px;
                font-family: 'SF Pro Display';
            }
            QLineEdit {
                background-color: white;
                border: 1px solid #D2D2D7;
                border-radius: 6px;
                padding: 5px;
                font-size: 13px;
                min-height: 25px;
            }
            QPushButton {
                background-color: #007AFF;
                color: white;
                border: none;
                border-radius: 6px;
                padding: 8px 16px;
                font-size: 13px;
                min-width: 80px;
            }
            QPushButton:hover {
                background-color: #0069D9;
            }
            QPushButton[text="Cancel"] {
                background-color: #E5E5EA;
                color: #1D1D1F;
            }
            QPushButton[text="Cancel"]:hover {
                background-color: #D1D1D6;
            }
        """)
        
        ok = dialog.exec_()
        group_name = dialog.textValue()
        
        if ok and group_name:
            # 显示加载状态
            self.loading_label.setText("正在添加群组，请稍候...")
            self.loading_label.show()
            self.status_label.setText("正在添加群组...")
            self.status_label.repaint()
            
            # 禁用相关按钮
            add_group_btn = self.findChild(QPushButton, "+")
            if add_group_btn:
                add_group_btn.setEnabled(False)
            
            try:
                # 异步添加群组
                success = await self.chat.add_group(group_name)
                
                if success:
                    self.group_list.addItem(group_name)
                    self.status_label.setText(f"已添加群组: {group_name}")
                else:
                    QMessageBox.warning(
                        self, 
                        "添加失败", 
                        f"无法添加群组: {group_name}",
                        QMessageBox.Ok,
                        QMessageBox.Ok
                    )
            finally:
                # 恢复状态显示和按钮状态
                self.loading_label.hide()
                if add_group_btn:
                    add_group_btn.setEnabled(True)
                trigger_word = self.trigger_edit.text().strip()
                self.status_label.setText(f"当前状态: {'运行中' if self.running else '未运行'} (触发词: @{trigger_word})")

    async def toggle_service(self):
        """异步切换服务状态"""
        if not self.running:
            # 检查是否有群组
            if not self.chat.get_groups():
                QMessageBox.warning(
                    self,
                    "提示",
                    "请先添加需要监听的群组",
                    QMessageBox.Ok,
                    QMessageBox.Ok
                )
                return
            
            # 显示加载状态
            self.loading_label.setText("正在启动服务，请稍候...")
            self.loading_label.show()
            self.status_label.setText("正在启动服务...")
            self.status_label.repaint()
            self.start_btn.setEnabled(False)
            
            try:
                if await self.chat.start():
                    self.running = True
                    self.start_btn.setText("停止监听")
                    self.start_btn.set_type("stop")
                    trigger_word = self.trigger_edit.text().strip()
                    self.status_label.setText(f"当前状态: 运行中 (触发词: @{trigger_word})")
                    # 使用应用程序的事件循环运行协程
                    self.app.run_coroutine(self.chat.process_messages())
                else:
                    self.status_label.setText("启动服务失败")
                    QMessageBox.warning(
                        self,
                        "错误",
                        "启动服务失败，请检查微信是否正常运行",
                        QMessageBox.Ok,
                        QMessageBox.Ok
                    )
            finally:
                self.loading_label.hide()
                self.start_btn.setEnabled(True)
        else:
            self.chat.stop()
            self.running = False
            self.start_btn.setText("开始监听")
            self.start_btn.set_type("primary")
            trigger_word = self.trigger_edit.text().strip()
            self.status_label.setText(f"当前状态: 已停止 (触发词: @{trigger_word})")

    def show_settings(self):
        """显示设置对话框"""
        dialog = SettingsDialog(self.config, self.chat, self)
        if dialog.exec_():
            self.update_group_list()

    def mousePressEvent(self, event):
        """处理鼠标按下事件"""
        if event.button() == Qt.LeftButton:
            self.drag_position = event.globalPos() - self.frameGeometry().topLeft()
            event.accept()

    def mouseMoveEvent(self, event):
        """处理鼠标移动事件"""
        if event.buttons() == Qt.LeftButton:
            self.move(event.globalPos() - self.drag_position)
            event.accept()

    def force_quit(self):
        """强制退出程序"""
        self.cleanup_and_quit()

    def closeEvent(self, event):
        """处理关闭事件"""
        try:
            print("正在关闭应用程序...")
            
            # 停止服务
            if self.running:
                self.chat.stop()
            
            # 保存设置
            self.save_window_settings()
            
            # 确保数据库连接关闭
            self.db.close()
            
            # 清理聊天管理器资源
            self.chat.cleanup()
            
            # 停止所有异步任务
            if hasattr(self.app, 'loop'):
                loop = self.app.loop
                # 取消所有正在运行的任务
                for task in asyncio.all_tasks(loop):
                    task.cancel()
                
                # 等待所有任务完成
                if loop.is_running():
                    loop.call_soon_threadsafe(loop.stop)
                    
                # 运行一次事件循环以确保任务被取消
                try:
                    loop.run_until_complete(asyncio.gather(*asyncio.all_tasks(loop), return_exceptions=True))
                except:
                    pass
                
                # 关闭事件循环
                try:
                    loop.close()
                except:
                    pass
            
            # 清理应用程序资源
            self.app.cleanup()
            
            # 确保Qt应用程序退出
            QApplication.quit()
            
            print("应用程序资源已清理完毕，正在退出...")
            
            # 使用定时器确保所有事件都被处理后再退出
            QTimer.singleShot(100, self._force_quit)
            
        except Exception as e:
            print(f"关闭应用程序时发生错误: {e}")
            self._force_quit()

    def _force_quit(self):
        """强制退出程序"""
        try:
            # 终止所有子进程
            import psutil
            current_process = psutil.Process()
            children = current_process.children(recursive=True)
            for child in children:
                try:
                    child.terminate()
                except:
                    pass
            
            # 等待子进程终止
            psutil.wait_procs(children, timeout=3)
            
            # 强制结束未终止的子进程
            for child in children:
                try:
                    if child.is_running():
                        child.kill()
                except:
                    pass
        except:
            pass
        
        # 强制退出主进程
        os._exit(0)

    def add_message(self, sender: str, content: str, is_reply: bool = False):
        """添加新消息到列表"""
        prefix = "🤖" if is_reply else "👤"
        item_text = f"{prefix} {sender}: {content}"
        # 添加到列表底部
        self.message_list.addItem(item_text)
        # 滚动到最新消息
        self.message_list.scrollToBottom()
        
        # 限制消息数量
        while self.message_list.count() > 100:
            self.message_list.takeItem(0)  # 移除最旧的消息

    def remove_group(self):
        """移除群组"""
        current_item = self.group_list.currentItem()
        if not current_item:
            QMessageBox.warning(self, "提示", "请先选择要移除的群组")
            return
            
        group_name = current_item.text()
        reply = QMessageBox.question(
            self,
            "确认移除",
            f"确定要移除群组 {group_name} 吗？",
            QMessageBox.Yes | QMessageBox.No,
            QMessageBox.No
        )
        
        if reply == QMessageBox.Yes:
            if self.chat.remove_group(group_name):
                self.group_list.takeItem(self.group_list.row(current_item))
                self.status_label.setText(f"已移除群组: {group_name}")
            else:
                QMessageBox.warning(self, "移除失败", f"无法移除群组: {group_name}")

    def update_service_status(self, is_running: bool):
        """更新服务状态"""
        self.running = is_running
        self.start_btn.setText("停止监听" if is_running else "开始监听")
        self.start_btn.set_type("stop" if is_running else "primary")  # 更新按钮样式
        trigger_word = self.trigger_edit.text().strip()
        self.status_label.setText(f"当前状态: {'运行中' if is_running else '已停止'} (触发词: @{trigger_word})") 