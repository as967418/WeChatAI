from sqlalchemy import create_engine, Column, Integer, String, DateTime, Text
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from datetime import datetime
import os

Base = declarative_base()

class ChatMessage(Base):
    __tablename__ = 'chat_messages'
    
    id = Column(Integer, primary_key=True)
    sender_id = Column(String(100))
    sender_name = Column(String(100))
    group_name = Column(String(100))
    message = Column(Text)
    reply = Column(Text)
    model = Column(String(100))
    mark = Column(String(100))
    created_at = Column(DateTime, default=datetime.now)

class DatabaseManager:
    def __init__(self):
        db_path = os.path.join('data', 'chat_history.db')
        os.makedirs('data', exist_ok=True)
        self.engine = create_engine(f'sqlite:///{db_path}')
        Base.metadata.create_all(self.engine)
        self.Session = sessionmaker(bind=self.engine)

    def add_message(self, sender_id, sender_name, group_name, message, reply, model, mark=""):
        """添加新的聊天记录"""
        session = self.Session()
        try:
            chat_message = ChatMessage(
                sender_id=sender_id,
                sender_name=sender_name,
                group_name=group_name,
                message=message,
                reply=reply,
                model=model,
                mark=mark
            )
            session.add(chat_message)
            session.commit()
            return True
        except Exception as e:
            print(f"保存聊天记录失败: {e}")
            session.rollback()
            return False
        finally:
            session.close()

    def get_messages(self, group_name=None, limit=50):
        """获取聊天记录"""
        session = self.Session()
        try:
            query = session.query(ChatMessage)
            if group_name:
                query = query.filter(ChatMessage.group_name == group_name)
            return query.order_by(ChatMessage.created_at.desc()).limit(limit).all()
        finally:
            session.close()

    def delete_messages(self, group_name=None, before_date=None):
        """删除聊天记录"""
        session = self.Session()
        try:
            query = session.query(ChatMessage)
            if group_name:
                query = query.filter(ChatMessage.group_name == group_name)
            if before_date:
                query = query.filter(ChatMessage.created_at < before_date)
            count = query.delete()
            session.commit()
            return count
        except Exception as e:
            print(f"删除聊天记录失败: {e}")
            session.rollback()
            return 0
        finally:
            session.close()

    def close(self):
        """关闭数据库连接"""
        try:
            if hasattr(self, 'conn'):
                self.conn.close()
        except Exception as e:
            print(f"关闭数据库连接失败: {e}") 