from sqlalchemy import Column,Boolean,Integer,String,ForeignKey,Float,Sequence
from sqlalchemy.orm import relationship
from sqlalchemy.sql.expression import null,text
from database import Base
from passlib.context import CryptContext

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


class sentiment_analysis(Base):
    __tablename__ = "sentiment_analysis"
    id = Column(Integer,primary_key=True,nullable=False,autoincrement=True)
    sender = Column(String,nullable=False)
    subject = Column(String,nullable=False)
    body = Column(String,nullable=False)
    appreciation = Column(String,nullable=False)
    category = Column(String,nullable=False)
    sentiment = Column(String,nullable=False)
    score = Column(Float, nullable=False)
    
class sentiment_analysis_counts(Base):
    __tablename__ = "sentiment_analysis_counts"
    id = Column(Integer,autoincrement=True,primary_key=True)
    email_id = Column(String,nullable=False)
    positive_count = Column(Integer,default=0)
    negative_count = Column(Integer,default=0)
    sentiment_analysis_id = Column(Integer, ForeignKey('sentiment_analysis.id'))
    sentiment_analysis = relationship("sentiment_analysis", backref="sentiment_analysis_counts")


class User(Base):
    __tablename__ = "register"
    id = Column(Integer,primary_key=True,index=True)
    email = Column(String,unique=True,nullable=False,index=True)
    password_hash = Column(String,nullable=False)
    is_active = Column(Boolean,default=True)


    def set_password(self, password: str):
        self.password_hash = pwd_context.hash(password)

    def check_password(self, password: str):
        return pwd_context.verify(password, self.password_hash)
