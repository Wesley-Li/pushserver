#!/usr/bin/env python
#coding:utf-8

from sqlalchemy.sql.expression import text, bindparam
from sqlalchemy.sql import select,insert, delete, update
from sqlalchemy.schema import Table
from sqlalchemy.orm import sessionmaker,scoped_session
from db import dba_logger,metadata#session
from datetime import datetime

class ExceptionHandler(object):
    
    try:
        _table=Table('exception_messages', metadata, autoload=True)
    except Exception,e:
        dba_logger.log(40,'Exception when logException(initing table):%s' % str(e))
            
    @classmethod
    def logException(cls,module,message,exctype='1',time=datetime.now()):
        """
        Used to insert exception info into database.
        
        Params:
            module : module name, indicating who raises the exception, e.g. android,ios,psg,adpns,db .etc
            exctype : exception type, 0 means service level while 1 is system level.
            message : exception description,length limit to 200 bytes
        """
        if None in (module,message,exctype,time):
            return False
        if type(module) != type('1') and type(module) != type(u'1'):
            return False
        if type(exctype) != type('1') and type(exctype) != type(u'1'):
            return False
        if type(time)!=datetime:
            return False
        if len(message)==0 or len(exctype)==0:
            return False
        if exctype not in ('0','1'):
            return False
        if len(module)==0:
            module='Unknown module'
        try:
            session = scoped_session(sessionmaker(bind=engine))
            i=cls._table.insert().values(
                                      module_name      = module[:80]      , 
                                      #module_name      = module[:80]      ,     
                                      exception_type   = exctype        ,
                                      messages         = message[:200]     ,  
                                      sent_time        = time,                                    
                                      ) 
        
            session.execute(i)
            session.commit()
            return True
        except Exception,e:
            dba_logger.log(40,'Exception when logException:%s' % str(e))
            dba_logger.log(20,'Exception detail:module_name(%s);exception_type(%s);messages(%s);sent_time(%s)' % (module,exctype,message,str(time)))
            session.rollback()
            return False


