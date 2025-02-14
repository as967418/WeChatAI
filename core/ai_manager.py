import os
from openai import OpenAI
import google.generativeai as genai
from typing import Dict, Optional
import json

class AIManager:
    def __init__(self, config_manager):
        self.config = config_manager
        self.chat_histories: Dict[str, list] = {}
        self.setup_models()

    def setup_models(self):
        """初始化各个AI模型的配置"""
        # 设置代理
        proxy = self.config.get_proxy()
        if proxy["http"]:
            os.environ["HTTP_PROXY"] = proxy["http"]
            os.environ["HTTPS_PROXY"] = proxy["https"]

        # 初始化DeepSeek
        self.deepseek_client = OpenAI(
            api_key=self.config.get_api_key("deepseek"),
            base_url="https://api.deepseek.com"
        )

        # 初始化Gemini
        genai.configure(api_key=self.config.get_api_key("gemini"))
        self.gemini_model = genai.GenerativeModel("gemini-1.5-flash")

        # 初始化通义千问
        self.qianwen_client = OpenAI(
            api_key=self.config.get_api_key("qianwen"),
            base_url="https://dashscope.aliyuncs.com/compatible-mode/v1"
        )

    def get_chat_history(self, group_name: str) -> list:
        """获取指定群的聊天历史"""
        if group_name not in self.chat_histories:
            system_prompt = self.config.get_system_prompt()
            self.chat_histories[group_name] = [
                {"role": "system", "content": system_prompt}
            ]
        return self.chat_histories[group_name]

    def update_chat_history(self, group_name: str, role: str, content: str):
        """更新聊天历史"""
        history = self.get_chat_history(group_name)
        history.append({"role": role, "content": content})
        
        # 保持历史记录在合理范围内（最近10条消息）
        if len(history) > 11:  # system消息+10条对话
            history = [history[0]] + history[-10:]
        self.chat_histories[group_name] = history

    async def get_ai_response(self, message: str, group_name: str, model: str = None) -> Optional[str]:
        """获取AI回复"""
        try:
            if not model:
                model = self.config.config["default_model"]

            history = self.get_chat_history(group_name)
            self.update_chat_history(group_name, "user", message)

            response = None
            if model == "deepseek":
                response = await self._call_deepseek(history)
            elif model == "gemini":
                response = await self._call_gemini(message)
            elif model == "qianwen":
                response = await self._call_qianwen(history)

            if response:
                self.update_chat_history(group_name, "assistant", response)
                return response
            return "AI 没有返回有效结果，请稍后再试"

        except Exception as e:
            print(f"AI调用失败: {str(e)}")
            return f"AI调用出错: {str(e)}"

    async def _call_deepseek(self, messages: list) -> Optional[str]:
        """调用DeepSeek API"""
        try:
            # 确保API密钥存在
            api_key = self.config.get_api_key("deepseek")
            if not api_key:
                print("DeepSeek API密钥未配置")
                return None

            # 设置API客户端
            self.deepseek_client = OpenAI(
                api_key=api_key,
                base_url="https://api.deepseek.com/v1"  # 修正API端点
            )

            # 调用API
            response = self.deepseek_client.chat.completions.create(
                model="deepseek-chat",
                messages=messages,
                temperature=0.7,
                max_tokens=2000  # 添加最大token限制
            )

            # 检查响应
            if response and response.choices and response.choices[0].message:
                return response.choices[0].message.content.strip()
            else:
                print("DeepSeek API返回空响应")
                return None

        except Exception as e:
            print(f"DeepSeek API调用详细错误: {str(e)}")
            return None

    async def _call_gemini(self, message: str) -> Optional[str]:
        """调用Gemini API"""
        try:
            response = self.gemini_model.generate_content(message)
            return response.text
        except Exception as e:
            print(f"Gemini API调用失败: {e}")
            return None

    async def _call_qianwen(self, messages: list) -> Optional[str]:
        """调用通义千问 API"""
        try:
            response = self.qianwen_client.chat.completions.create(
                model="qwen-turbo",
                messages=messages
            )
            return response.choices[0].message.content.strip()
        except Exception as e:
            print(f"通义千问API调用失败: {e}")
            return None

    def clear_chat_history(self, group_name: str):
        """清除指定群的聊天历史"""
        if group_name in self.chat_histories:
            system_prompt = self.config.get_system_prompt()
            self.chat_histories[group_name] = [
                {"role": "system", "content": system_prompt}
            ] 