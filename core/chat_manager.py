from wxauto import WeChat
import asyncio
from typing import List, Optional, NamedTuple
import time
import re
import traceback
from concurrent.futures import ThreadPoolExecutor
import threading

class Message(NamedTuple):
    """消息数据类"""
    sender: str
    content: str
    room_id: str

class ChatManager:
    def __init__(self, config_manager, ai_manager, db_manager):
        self.config = config_manager
        self.ai = ai_manager
        self.db = db_manager
        self.wx = WeChat()  # 直接初始化 WeChat 实例
        self.running = False
        self.groups = set(self.config.get_groups())  # 从配置中加载群组
        self._task = None
        self.main_window = None
        self.last_messages = {group: set() for group in self.groups}  # 为每个群初始化消息集合

    async def add_group(self, group_name: str) -> bool:
        """添加监听群组"""
        try:
            if group_name not in self.groups:
                # 直接添加群组
                self.wx.AddListenChat(who=group_name, savepic=False)
                
                self.groups.add(group_name)
                self.last_messages[group_name] = set()  # 初始化消息集合
                
                # 保存配置
                groups = list(self.groups)
                self.config.set_groups(groups)
                print(f"成功添加群组: {group_name}")
                return True
            return False
        except Exception as e:
            print(f"添加群组失败: {e}")
            # 清理失败的添加
            if group_name in self.groups:
                self.groups.remove(group_name)
            if group_name in self.last_messages:
                del self.last_messages[group_name]
            return False

    async def start(self) -> bool:
        """启动聊天管理器"""
        if self.running:
            return False
        
        try:
            print("微信登录账号:", self.wx.nickname)
            
            # 初始化监听
            for group in self.groups:
                self.wx.AddListenChat(who=group, savepic=False)
                if group not in self.last_messages:
                    self.last_messages[group] = set()
                print(f"已开始监听微信群: {group}")
            
            self.running = True
            return True
        except Exception as e:
            print(f"启动失败: {e}")
            self.running = False
            return False

    def stop(self):
        """停止聊天管理器"""
        try:
            print("正在停止聊天管理器...")
            self.running = False
            
            # 取消异步任务
            if self._task:
                self._task.cancel()
                self._task = None
            
            # 清理消息记录
            self.last_messages.clear()
            
            # 移除所有监听
            for group in self.groups:
                try:
                    self.wx.RemoveListenChat(group)
                except:
                    pass
            
            print("聊天管理器已停止")
            
        except Exception as e:
            print(f"停止聊天管理器时发生错误: {e}")

    def cleanup(self):
        """清理资源"""
        try:
            self.stop()
            self.groups.clear()
            self.last_messages.clear()
        except Exception as e:
            print(f"清理资源时发生错误: {e}")

    async def process_messages(self):
        """处理消息的主循环"""
        try:
            while self.running:
                try:
                    # 获取所有监听消息
                    msgs = self.wx.GetListenMessage()
                    if msgs:
                        for chat in msgs:
                            group_name = next((group for group in self.groups if group in str(chat)), None)
                            if not group_name:
                                continue

                            one_msgs = msgs.get(chat)
                            for msg_data in one_msgs:
                                try:
                                    # 生成消息唯一标识
                                    msg_id = f"{msg_data.sender}_{msg_data.content}_{time.time()}"
                                    
                                    # 检查是否是新消息
                                    if msg_id in self.last_messages[group_name]:
                                        continue
                                        
                                    # 添加到已处理集合
                                    self.last_messages[group_name].add(msg_id)
                                    # 保持集合大小在合理范围
                                    if len(self.last_messages[group_name]) > 100:
                                        self.last_messages[group_name] = set(list(self.last_messages[group_name])[-50:])

                                    # 跳过自己发送的消息
                                    if msg_data.sender == 'Self':
                                        continue

                                    # 创建消息对象
                                    msg = Message(
                                        sender=msg_data.sender,
                                        content=msg_data.content,
                                        room_id=group_name
                                    )
                                    
                                    # 处理消息
                                    await self.handle_message(msg, group_name)

                                except Exception as e:
                                    print(f"处理单条消息错误: {e}")
                                    traceback.print_exc()

                except Exception as e:
                    error_msg = str(e)
                    print(f"消息处理循环错误: {error_msg}")
                    
                    # 检查是否是微信窗口关闭错误
                    if "事件无法调用任何订户" in error_msg or "-2147220991" in error_msg:
                        print("检测到微信窗口已关闭，停止监听...")
                        if self.main_window:
                            self.main_window.add_message("系统", "检测到微信窗口已关闭，已停止监听", True)
                            # 在主线程中更新UI
                            await asyncio.get_event_loop().run_in_executor(
                                None, 
                                self.main_window.update_service_status,
                                False
                            )
                        self.running = False
                        break

                    # 其他错误，等待一段时间后继续
                    await asyncio.sleep(5)
                    continue

                # 正常等待时间
                await asyncio.sleep(2)

        except asyncio.CancelledError:
            print("消息处理任务被取消")
        except Exception as e:
            print(f"消息处理主循环错误: {e}")
            traceback.print_exc()
        finally:
            self.running = False
            if self.main_window:
                self.main_window.add_message("系统", "消息监听已停止", True)
                # 在主线程中更新UI
                try:
                    await asyncio.get_event_loop().run_in_executor(
                        None, 
                        self.main_window.update_service_status,
                        False
                    )
                except:
                    pass

    async def handle_message(self, msg, group_name: str):
        """处理单条消息"""
        try:
            # 跳过系统消息
            if msg.sender == "SYS" or "以下为新消息" in msg.content:
                return

            # 获取自定义触发词和默认触发词
            custom_trigger = self.config.get_trigger_word()
            default_triggers = ['victorAI', '@victorAI']
            
            # 检查是否包含触发词
            has_trigger = (
                f'@{custom_trigger}' in msg.content or 
                msg.content.lower().startswith(custom_trigger.lower()) or 
                '@victorAI' in msg.content or 
                msg.content.lower().startswith('victorai')
            )
            
            if not has_trigger:
                return
            
            # 提取实际的消息内容，移除所有可能的触发词
            content = msg.content
            # 移除自定义触发词（区分大小写）
            content = content.replace(f'@{custom_trigger}', '').replace(custom_trigger, '')
            # 移除默认触发词（不区分大小写）
            for trigger in default_triggers:
                pattern = re.compile(re.escape(trigger), re.IGNORECASE)
                content = pattern.sub('', content)
            
            # 清理并去除首尾空格
            content = content.strip()
            
            if not content:
                return

            print(f"收到消息 - 群: {group_name}, 发送者: {msg.sender}, 内容: {content}")
            
            # 显示接收到的消息
            if self.main_window:
                self.main_window.add_message(msg.sender, content)

            # 获取AI回复
            model = self.config.config["default_model"]
            reply = await self.ai.get_ai_response(content, group_name, model)

            if reply:
                # 发送回复
                self.wx.SendMsg(reply, group_name)
                print(f"已回复 - 群: {group_name}, 内容: {reply}")
                
                # 显示回复消息
                if self.main_window:
                    self.main_window.add_message("AI助手", reply, True)

                # 保存到数据库
                self.db.add_message(
                    sender_id=msg.sender,
                    sender_name=msg.sender,
                    group_name=group_name,
                    message=content,
                    reply=reply,
                    model=model
                )

        except Exception as e:
            print(f"消息处理失败: {e}")
            error_msg = f"消息处理出错: {str(e)}"
            self.wx.SendMsg(error_msg, group_name)
            if self.main_window:
                self.main_window.add_message("系统", error_msg, True)

    def remove_group(self, group_name: str) -> bool:
        """移除监听群组"""
        try:
            if group_name in self.groups:
                # 从监听列表移除
                self.groups.remove(group_name)
                # 清理消息记录
                if group_name in self.last_messages:
                    del self.last_messages[group_name]
                # 保存配置
                groups = list(self.groups)
                self.config.set_groups(groups)
                print(f"成功移除群组: {group_name}")
                return True
            return False
        except Exception as e:
            print(f"移除群组失败: {e}")
            return False

    def get_groups(self) -> List[str]:
        """获取当前监听的群组列表"""
        return list(self.groups)

    def set_main_window(self, window):
        """设置主窗口引用"""
        self.main_window = window 