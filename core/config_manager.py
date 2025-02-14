import os
from pathlib import Path
from dotenv import load_dotenv
import json

class ConfigManager:
    def __init__(self):
        self.config_file = Path("data/config.json")
        self.load_env()
        self.load_config()
        self.ensure_data_dir()

    def ensure_data_dir(self):
        """确保数据目录存在"""
        data_dir = Path("data")
        data_dir.mkdir(exist_ok=True)
        if not self.config_file.exists():
            self.save_config()

    def load_env(self):
        """加载环境变量"""
        load_dotenv()
        self.default_config = {
            "ai_settings": {
                "deepseek": {
                    "api_key": os.getenv("DEEPSEEK_API_KEY", ""),
                    "model": "deepseek-chat",
                    "temperature": 0.7
                },
                "gemini": {
                    "api_key": os.getenv("GEMINI_API_KEY", ""),
                    "model": "gemini-1.5-flash"
                },
                "qianwen": {
                    "api_key": os.getenv("QIANWEN_API_KEY", ""),
                    "model": "qwen-turbo"
                }
            },
            "proxy": {
                "http": os.getenv("HTTP_PROXY", ""),
                "https": os.getenv("HTTPS_PROXY", "")
            },
            "system_prompt": os.getenv("SYSTEM_PROMPT", "你是AI助手，名字叫VictorAI"),
            "groups": [],
            "default_model": "deepseek",
            "trigger_word": "AI",
            "window_settings": {
                "always_on_top": True,
                "position": {"x": 0, "y": 0}
            }
        }

    def load_config(self):
        """加载配置文件"""
        try:
            if self.config_file.exists():
                with open(self.config_file, 'r', encoding='utf-8') as f:
                    self.config = json.load(f)
            else:
                self.config = self.default_config
                self.save_config()
        except Exception as e:
            print(f"加载配置文件失败: {e}")
            self.config = self.default_config

    def save_config(self):
        """保存配置到文件"""
        try:
            self.config_file.parent.mkdir(parents=True, exist_ok=True)
            with open(self.config_file, 'w', encoding='utf-8') as f:
                json.dump(self.config, f, ensure_ascii=False, indent=4)
        except Exception as e:
            print(f"保存配置文件失败: {e}")

    def get_api_key(self, model):
        """获取指定模型的API密钥"""
        return self.config["ai_settings"].get(model, {}).get("api_key", "")

    def set_api_key(self, model, api_key):
        """设置指定模型的API密钥"""
        if model in self.config["ai_settings"]:
            self.config["ai_settings"][model]["api_key"] = api_key
            self.save_config()

    def get_proxy(self):
        """获取代理设置"""
        return self.config["proxy"]

    def set_proxy(self, http_proxy, https_proxy):
        """设置代理"""
        self.config["proxy"]["http"] = http_proxy
        self.config["proxy"]["https"] = https_proxy
        self.save_config()

    def get_groups(self) -> list:
        """获取群组列表"""
        return self.config.get("groups", [])

    def set_groups(self, groups: list):
        """设置群组列表"""
        self.config["groups"] = groups
        self.save_config()

    def get_system_prompt(self):
        """获取系统提示词"""
        return self.config["system_prompt"]

    def set_system_prompt(self, prompt):
        """设置系统提示词"""
        self.config["system_prompt"] = prompt
        self.save_config()

    def get_window_settings(self):
        """获取窗口设置"""
        return self.config["window_settings"]

    def set_window_settings(self, settings):
        """设置窗口配置"""
        self.config["window_settings"] = settings
        self.save_config()

    def get_trigger_word(self):
        """获取触发词"""
        return self.config.get("trigger_word", "AI")

    def set_trigger_word(self, word):
        """设置触发词"""
        self.config["trigger_word"] = word
        self.save_config() 