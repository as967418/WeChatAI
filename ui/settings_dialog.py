from PySide6.QtWidgets import (QDialog, QVBoxLayout, QHBoxLayout, QLabel, 
                             QLineEdit, QTextEdit, QPushButton, QComboBox,
                             QTabWidget, QWidget, QListWidget, QInputDialog,
                             QCheckBox, QGridLayout, QFrame)

class SettingsDialog(QDialog):
    def __init__(self, config_manager, chat_manager, parent=None):
        super().__init__(parent)
        self.config = config_manager
        self.chat = chat_manager
        self.setup_ui()
        self.load_settings()
        self.apply_mac_style()

    def apply_mac_style(self):
        """应用类似macOS的样式"""
        self.setStyleSheet("""
            QDialog {
                background-color: #F5F5F7;
            }
            QWidget {
                font-family: 'SF Pro Display';
            }
            QLabel {
                color: #1D1D1F;
                font-size: 13px;
            }
            QLineEdit, QTextEdit {
                background-color: white;
                border: 1px solid #D2D2D7;
                border-radius: 6px;
                padding: 5px;
                font-size: 13px;
            }
            QComboBox {
                background-color: white;
                border: 1px solid #D2D2D7;
                border-radius: 6px;
                padding: 5px;
                min-height: 30px;
            }
            QTabWidget::pane {
                border: 1px solid #D2D2D7;
                border-radius: 8px;
                background-color: white;
            }
            QTabBar::tab {
                background-color: #F5F5F7;
                border: none;
                padding: 8px 16px;
                margin-right: 2px;
                border-top-left-radius: 6px;
                border-top-right-radius: 6px;
            }
            QTabBar::tab:selected {
                background-color: white;
                color: #007AFF;
            }
            QPushButton {
                background-color: #007AFF;
                color: white;
                border: none;
                border-radius: 6px;
                padding: 8px 16px;
                font-size: 13px;
            }
            QPushButton:hover {
                background-color: #0069D9;
            }
            QPushButton[text="取消"] {
                background-color: #E5E5EA;
                color: #1D1D1F;
            }
            QPushButton[text="取消"]:hover {
                background-color: #D1D1D6;
            }
        """)

    def setup_ui(self):
        """设置UI界面"""
        self.setWindowTitle("设置")
        self.resize(320, 400)
        layout = QVBoxLayout(self)
        layout.setContentsMargins(8, 8, 8, 8)
        layout.setSpacing(8)

        # 创建标签页
        tab_widget = QTabWidget()
        layout.addWidget(tab_widget)

        # API设置页
        api_tab = QWidget()
        api_layout = QVBoxLayout(api_tab)
        api_layout.setContentsMargins(5, 5, 5, 5)
        api_layout.setSpacing(8)
        
        # 默认模型选择
        model_layout = QHBoxLayout()
        model_layout.addWidget(QLabel("默认模型:"))
        self.model_combo = QComboBox()
        self.model_combo.addItems(["deepseek", "gemini", "qianwen"])
        model_layout.addWidget(self.model_combo)
        api_layout.addLayout(model_layout)

        # DeepSeek设置
        api_layout.addWidget(QLabel("DeepSeek API Key:"))
        self.deepseek_key = QLineEdit()
        api_layout.addWidget(self.deepseek_key)

        # Gemini设置
        api_layout.addWidget(QLabel("Gemini API Key:"))
        self.gemini_key = QLineEdit()
        api_layout.addWidget(self.gemini_key)
        
        # Gemini代理设置
        self.gemini_proxy_check = QCheckBox("启用代理")
        api_layout.addWidget(self.gemini_proxy_check)
        
        proxy_widget = QWidget()
        proxy_layout = QGridLayout(proxy_widget)
        proxy_layout.setContentsMargins(10, 0, 0, 0)
        proxy_layout.setSpacing(5)
        
        proxy_layout.addWidget(QLabel("HTTP:"), 0, 0)
        self.http_proxy = QLineEdit()
        proxy_layout.addWidget(self.http_proxy, 0, 1)
        
        proxy_layout.addWidget(QLabel("HTTPS:"), 1, 0)
        self.https_proxy = QLineEdit()
        proxy_layout.addWidget(self.https_proxy, 1, 1)
        
        api_layout.addWidget(proxy_widget)

        # 通义千问设置
        api_layout.addWidget(QLabel("通义千问 API Key:"))
        self.qianwen_key = QLineEdit()
        api_layout.addWidget(self.qianwen_key)
        
        api_layout.addStretch()
        tab_widget.addTab(api_tab, "模型设置")

        # 系统提示词设置页
        prompt_tab = QWidget()
        prompt_layout = QVBoxLayout(prompt_tab)
        prompt_layout.setContentsMargins(5, 5, 5, 5)
        
        self.system_prompt = QTextEdit()
        self.system_prompt.setPlaceholderText("请输入系统提示词...")
        prompt_layout.addWidget(self.system_prompt)
        
        tab_widget.addTab(prompt_tab, "提示词设置")

        # 确定取消按钮
        button_layout = QHBoxLayout()
        button_layout.setSpacing(8)
        save_btn = QPushButton("保存")
        save_btn.clicked.connect(self.save_settings)
        cancel_btn = QPushButton("取消")
        cancel_btn.clicked.connect(self.reject)
        button_layout.addWidget(save_btn)
        button_layout.addWidget(cancel_btn)
        layout.addLayout(button_layout)

        # 设置固定大小
        self.setFixedSize(self.size())

    def load_settings(self):
        """加载设置"""
        # API设置
        self.deepseek_key.setText(self.config.get_api_key("deepseek"))
        self.gemini_key.setText(self.config.get_api_key("gemini"))
        self.qianwen_key.setText(self.config.get_api_key("qianwen"))
        
        # 代理设置
        proxy = self.config.get_proxy()
        self.gemini_proxy_check.setChecked(bool(proxy.get("http") or proxy.get("https")))
        self.http_proxy.setText(proxy.get("http", ""))
        self.https_proxy.setText(proxy.get("https", ""))
        
        # 启用/禁用代理输入框
        self.http_proxy.setEnabled(self.gemini_proxy_check.isChecked())
        self.https_proxy.setEnabled(self.gemini_proxy_check.isChecked())
        
        # 默认模型
        default_model = self.config.config.get("default_model", "deepseek")
        index = self.model_combo.findText(default_model)
        if index >= 0:
            self.model_combo.setCurrentIndex(index)

        # 系统提示词
        self.system_prompt.setText(self.config.get_system_prompt())

        # 连接代理复选框信号
        self.gemini_proxy_check.stateChanged.connect(self._on_proxy_check_changed)

    def _on_proxy_check_changed(self, state):
        """处理代理复选框状态变化"""
        enabled = bool(state)
        self.http_proxy.setEnabled(enabled)
        self.https_proxy.setEnabled(enabled)
        if not enabled:
            self.http_proxy.clear()
            self.https_proxy.clear()

    def save_settings(self):
        """保存设置"""
        # API设置
        self.config.set_api_key("deepseek", self.deepseek_key.text())
        self.config.set_api_key("gemini", self.gemini_key.text())
        self.config.set_api_key("qianwen", self.qianwen_key.text())
        
        # 代理设置
        if self.gemini_proxy_check.isChecked():
            self.config.set_proxy(self.http_proxy.text(), self.https_proxy.text())
        else:
            self.config.set_proxy("", "")

        # 默认模型
        self.config.config["default_model"] = self.model_combo.currentText()
        self.config.save_config()

        # 系统提示词
        self.config.set_system_prompt(self.system_prompt.toPlainText())

        self.accept() 