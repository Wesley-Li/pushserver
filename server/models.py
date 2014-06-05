from sqlalchemy import create_engine,ForeignKey
from sqlalchemy.orm import relationship
from sqlalchemy import Column, Integer, String, Table

from sqlalchemy.ext.declarative import declarative_base
Base = declarative_base()

association_table = Table('association', Base.metadata,
    Column('app_id', Integer, ForeignKey('app.id')),
    Column('device_id', Integer, ForeignKey('device.id'))
)

class App(Base):
    __tablename__ = 'app'
    id = Column(Integer,primary_key=True)
    name = Column(String(50),nullable=False,unique=True)
    devices = relationship("Device",secondary=association_table,backref="apps")
    
    def __init__(self,name):
        self.name=name

    def __repr__(self):
        return "<App('%s')>" % self.name

    
class Device(Base):
    __tablename__ = 'device'
    id = Column(Integer,primary_key=True)
    devicetoken = Column(String(50),nullable=False,unique=True)
    #assocs = relationship("Association",backref="devices")
    #name = Column(String(50),nullable=False)
    
    def __init__(self,devicetoken):
        self.devicetoken = devicetoken

    def __repr__(self):
        return "<Device('%s')>" % self.devicetoken

#def create_all():
#    metadata.create_all(engine)

if __name__=='__main__':
    #create_all()
    pass