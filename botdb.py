#usr/bin/env python
#coding:utf8

import sqlalchemy
from sqlalchemy import create_engine,update
from sqlalchemy import Column, Integer, String, Text, DateTime
from sqlalchemy.orm import scoped_session, sessionmaker
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship

engine = create_engine('sqlite:///botdb2.sqlite')

db_session = scoped_session(sessionmaker(bind=engine))

Base = declarative_base()
Base.query  = db_session.query_property()

class Session(Base):
    __tablename__ = 'sessions'

    user_id = Column(Integer, primary_key=True)
    update_id = Column(Integer)
    chat_id = Column(Integer)
    user_name = Column(String(10))
    first_name = Column(String(20))
    last_name = Column(String(30))
    data = Column(String(100))

    def __init__(self, user_id=None, chat_id=None, update_id=None, user_name=None, first_name=None, last_name=None, data=None):
        print(user_id)
        self.user_id = user_id
        self.chat_id = chat_id
        self.update_id = update_id
        #self.user_name = user_name
        self.first_name = first_name
        #self.last_name = last_name
        self.data = data

    def __repr__(self):
        print('NEWNEW')
        return '<User {} {} {} {}>'.format(self.user_id, self.chat_id, self.update_id, self.first_name, self.data)



if __name__ == '__main__':
    Base.metadata.create_all(bind=engine)
