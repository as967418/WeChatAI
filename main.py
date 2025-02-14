import sys
import asyncio
import signal
import os
from PySide6.QtWidgets import QApplication
from PySide6.QtCore import QTimer
from PySide6.QtGui import QIcon
from core.config_manager import ConfigManager
from core.database_manager import DatabaseManager
from core.ai_manager import AIManager
from core.chat_manager import ChatManager
from ui.main_window import MainWindow
import resources_rc

class AsyncApplication(QApplication):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.loop = asyncio.new_event_loop()
        asyncio.set_event_loop(self.loop)
        self.async_timer = QTimer()
        self.async_timer.timeout.connect(self._process_async_events)
        self.async_timer.start(10)
        
        # 注册信号处理
        signal.signal(signal.SIGINT, self.signal_handler)
        signal.signal(signal.SIGTERM, self.signal_handler)

    def signal_handler(self, signum, frame):
        """处理系统信号"""
        print(f"收到信号: {signum}")
        self.cleanup()
        os._exit(0)

    def _process_async_events(self):
        try:
            self.loop.stop()
            self.loop.run_forever()
        except Exception as e:
            print(f"异步事件处理错误: {e}")

    def run_coroutine(self, coro):
        """运行协程"""
        return asyncio.run_coroutine_threadsafe(coro, self.loop)

    def cleanup(self):
        """清理资源"""
        try:
            print("正在清理应用程序资源...")
            
            # 停止异步定时器
            if hasattr(self, 'async_timer'):
                self.async_timer.stop()
                self.async_timer.deleteLater()
            
            # 确保事件循环停止
            if hasattr(self, 'loop') and self.loop.is_running():
                self.loop.call_soon_threadsafe(self.loop.stop)
            
            # 取消所有异步任务
            if hasattr(self, 'loop'):
                pending = asyncio.all_tasks(self.loop)
                if pending:
                    # 取消所有任务
                    for task in pending:
                        task.cancel()
                    
                    # 等待任务取消完成
                    try:
                        self.loop.run_until_complete(asyncio.gather(*pending, return_exceptions=True))
                    except:
                        pass
                
                # 关闭事件循环
                try:
                    self.loop.close()
                except:
                    pass
            
            # 终止所有子进程
            try:
                import psutil
                current_process = psutil.Process()
                children = current_process.children(recursive=True)
                for child in children:
                    try:
                        child.terminate()
                    except:
                        pass
                psutil.wait_procs(children, timeout=3)
            except:
                pass
            
            print("应用程序资源清理完成")
            
        except Exception as e:
            print(f"清理资源时发生错误: {e}")

def main():
    try:
        # 创建事件循环
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)

        # 创建应用程序
        app = AsyncApplication(sys.argv)

        # 初始化各个管理器
        config_manager = ConfigManager()
        db_manager = DatabaseManager()
        ai_manager = AIManager(config_manager)
        chat_manager = ChatManager(config_manager, ai_manager, db_manager)

        # 创建主窗口
        window = MainWindow(config_manager, chat_manager, db_manager, app)
        app.setWindowIcon(QIcon(":bot.ico"))  # 设置任务栏图标
        chat_manager.set_main_window(window)
        window.show()

        # 运行应用程序
        return app.exec()

    except Exception as e:
        print(f"程序运行错误: {e}")
        return 1

if __name__ == "__main__":
    sys.exit(main()) 