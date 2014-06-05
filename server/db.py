from settings import db_url,engine_echo,pool_rec,pool_recycle_time#,dba_logger
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker,scoped_session
from sqlalchemy.schema import MetaData,Table

engine = create_engine(db_url, pool_size=100,max_overflow=150,echo=engine_echo,pool_recycle=3600)
session = scoped_session(sessionmaker(bind=engine))
metadata = MetaData(bind=engine)
 
from tornado.ioloop import PeriodicCallback
from sqlalchemy.exc import InvalidRequestError,StatementError,OperationalError

import utils
dba_logger = utils.Logger.createLogger('db',fd='./logs/db.log')

tables = {'sessions_details':Table('sessions_details', metadata, autoload=True),
          'messages':Table('messages', metadata, autoload=True),
          'messages_details':Table('messages_details', metadata, autoload=True)
          }
def _ping_db():
    #session.execute('show variables')
    try:
        session.execute('select 1')
    except (InvalidRequestError,StatementError,OperationalError),e:
        dba_logger.log(30,'Exception when pinging db:%s' % str(e))
        session.rollback()

if pool_rec:
    # ping db, so that mysql won't goaway
    PeriodicCallback(_ping_db, pool_recycle_time * 1000).start()



