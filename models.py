# models.py
from sqlalchemy import Column, Integer, String, DateTime, Text, Boolean, Float
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.dialects.postgresql import UUID
import uuid
import datetime

Base = declarative_base()

class ChatLog(Base):
    __tablename__ = 'chat_logs'
    id = Column(Integer, primary_key=True)
    user_id = Column(UUID(as_uuid=True), default=uuid.uuid4, nullable=False)
    timestamp = Column(DateTime, default=datetime.datetime.utcnow)
    step_number = Column(Integer)
    question_number = Column(Integer)
    question_id = Column(String, default='')
    message_id = Column(Integer)
    role = Column(String(50))
    content = Column(Text)
    errors = Column(Integer)
    flag = Column(Boolean)
    reasoning = Column(Text)
    complete = Column(Boolean, default=False)
    end_script = Column(Boolean, default=False)
    # max_tokens = Column(Integer)
    # model = Column(String(50))
    # temperature = Column(Float)
    # top_p = Column(Float)
    # # models.py
# from sqlalchemy import Column, Integer, String, DateTime, Text
# from sqlalchemy.ext.declarative import declarative_base
# from sqlalchemy.dialects.postgresql import UUID
# import uuid
# import datetime

# Base = declarative_base()

# class ChatLog(Base):
#     __tablename__ = 'chat_logs'
#     id = Column(Integer, primary_key=True)
#     user_id = Column(UUID(as_uuid=True), default=uuid.uuid4, nullable=False)
#     timestamp = Column(DateTime, default=datetime.datetime.utcnow)
#     step_number = Column(Integer)
#     question_number = Column(Integer)
#     message_id = Column(Integer)
#     role = Column(String)
#     content = Column(Text)
#     errors = Column(Integer)
#     flag = Column(String)
#     reasoning = Column(Text)
