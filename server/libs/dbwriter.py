#!/usr/bin/env python
#coding: utf-8

from sqlalchemy.sql.expression import text, bindparam
from sqlalchemy.sql import select,insert, delete, update
from sqlalchemy.schema import Table
from sqlalchemy.orm import sessionmaker,scoped_session
from db import dba_logger,metadata,engine#session
from datetime import datetime
from exctrace import exctrace
from sqlalchemy import and_

direct_engine = True
use_raw = False

#import gevent  
#from gevent import monkey
#monkey.patch_all()

class DBWriter(object):
    
    def __init__(self,tablename):
        
        self.tablename = tablename
        try:
            self._table=Table(tablename, metadata, autoload=True)
        except Exception,e:
            exctrace('db','1','DBWriter init failed',dba_logger,'DBWriter init failed','Exception when DBWriter initing table:%s' % str(e))
            #dba_logger.log(40,'Exception when DBWriter initing table:%s' % str(e))   
    
    def dbwrite(self,**kwargs):
        """
        Used to insert exception info into database.
        
        Params:
            module : module name, indicating who raises the exception, e.g. android,ios,psg,adpns,db .etc
            type : exception type, 0 means service level while 1 is system level.
            message : exception description,length limit to 256 bytes
        """
        try:
            
            i=self._table.insert().values(**kwargs) 
            if direct_engine:
                engine.execute(i)
                #gevent.spawn(engine.execute,i)
                #gevent.sleep(0)
                #gevent.joinall([gevent.spawn(engine.execute,i)])
            else:
                session = scoped_session(sessionmaker(bind=engine))
                session.execute(i)
                session.commit()
                session.close()
        except Exception,e:
            #dba_logger.log(40,'Exception when dbwriter:%s' % str(e))
            #dba_logger.log(20,'Exception detail:%s' % str(kwargs))
            exctrace('db','1','Error happened when writing db',dba_logger,'Exception when dbwriter:%s' % str(e),'Exception detail:%s' % str(kwargs))
            if not direct_engine:
                session.rollback()
                session.close()
    
    def dbupdate(self,whereclause,**kwargs):
        """
        Used to insert exception info into database.
        
        Params:
            module : module name, indicating who raises the exception, e.g. android,ios,psg,adpns,db .etc
            type : exception type, 0 means service level while 1 is system level.
            message : exception description,length limit to 256 bytes
        """
        try:
            
            i=self._table.update().values(**kwargs).where(whereclause) 
            if direct_engine:
                engine.execute(i)
                #gevent.spawn(engine.execute,i)
            else:
                session = scoped_session(sessionmaker(bind=engine))
                session.execute(i)
                session.commit()
                session.close()
        except Exception,e:
            #dba_logger.log(40,'Exception when dbwriter:%s' % str(e))
            #dba_logger.log(20,'Exception detail:%s' % str(kwargs))
            exctrace('db','1','Error happened when updating db',dba_logger,'Exception when dbupdate:%s' % str(e),'Exception detail:%s' % str(kwargs))
            if not direct_engine:
                session.rollback()
                session.close()
            
    def dbquery(self,whereclause):
        try:
            
            i=self._table.select().where(whereclause) 
            if direct_engine:
                res = engine.execute(i)
                return res
            else:
                session = scoped_session(sessionmaker(bind=engine))
                res = session.execute(i)
                return res
                session.close()
        except Exception,e:
            #dba_logger.log(40,'Exception when dbwriter:%s' % str(e))
            #dba_logger.log(20,'Exception detail:%s' % str(kwargs))
            exctrace('db','1','Error happened when querying db',dba_logger,'Exception when dbquery:%s' % str(e),'Exception detail:%s' % str(whereclause))
            #session.rollback()
            if not direct_engine:
                session.close()
        #res = session.execute(connection_writer._table.select().where(connection_writer._table.c.app_key==self.app_key).where(connection_writer._table.c.device_token==self._devicetoken))
    
            
messages_writer = DBWriter('messages')
connection_writer = DBWriter('sessions_details')
messages_details_writer = DBWriter('messages_details')

