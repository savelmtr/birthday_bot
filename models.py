from sqlalchemy import Column, ForeignKey, Integer, String, Date, BigInteger
from sqlalchemy.ext.declarative import declarative_base


Base = declarative_base()


class Groups(Base):
    __tablename__ = 'groups'
    id = Column(BigInteger, primary_key=True, autoincrement=True)
    userid = Column(BigInteger, ForeignKey("users.id"), primary_key=True)


class Users(Base):
    __tablename__ = 'users'
    id = Column(BigInteger, primary_key=True)
    username = Column(String, nullable=False)
    first_name = Column(String, nullable=False, default='')
    last_name = Column(String, nullable=False, default='')
    wish_string = Column(String, nullable=False, default='')
    birthday = Column(Date)
