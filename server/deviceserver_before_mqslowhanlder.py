#!/usr/bin/env python
#coding:utf-8

import socket
from tornado import process
from tornado import netutil
from tornado.tcpserver import TCPServer
from tornado import ioloop
from tornado import stack_context
from tornado.iostream import StreamClosedError
import time,uuid,hashlib
import datetime
import re
import json
import sys
import zmq
from threading import Timer,Thread
import settings
import utils
from db import session,dba_logger
from models import Device

from sqlalchemy.orm.exc import NoResultFound
from sqlalchemy.orm.exc import MultipleResultsFound
import functools
from Queue import Queue
from libs.dbwriter import connection_writer,messages_writer,messages_details_writer
from sqlalchemy.sql import select,insert, delete, update
from sqlalchemy import and_
from libs.exctrace import exctrace
from exception_handler import ExceptionHandler
from functools import partial
#from tornado.process_work import TWork
#port = 21567
#port2 = 21568
#clients = {}
debug = settings.deviceserver_debug

debug2 = False

logger = utils.Logger.createLogger('devsrv',fd='./logs/deviceserv.log')
#db_logger = utils.Logger.createLogger('db',fd='./logs/db.log')
db_logger = dba_logger

msg_format = '{"msg":\"%s\","id":%s,"flag":"*#*"}'
msg_format_http = '{"id":\"%s\","flag":"*#*"}'
#feed_pattern = re.compile()

#class ServerHandler(object):
#    @staticmethod
def response(fd,event):
    if event & ioloop.IOLoop.READ:
        print "Incoming data from", clients[fd]['address']
        data = clients[fd]['connection'].socket.recv(1024)
        loopone.update_handler(fd, ioloop.IOLoop.WRITE)
        #ep.modify(fd,select.EPOLLOUT)

        # Zero length = remote closure.
        if not data:
            print "Remote close on ", clients[fd]['address']
            #ep.modify(fd, 0)
            #clients[fd]['connection'].shutdown(socket.SHUT_RDWR)
            #ioloop.IOLoop.instance().remove_handler(fd)
            #clients[fd]['connection'].socket.shutdown(socket.SHUT_RDWR)
            loopone.remove_handler(fd)
            del clients[fd]
        # Store the input.
        else:
            pass
            #print 'data is',str(data)
    elif event & ioloop.IOLoop.WRITE:
        print "Writing data to", clients[fd]['address']
        clients[fd]['connection'].socket.send(clients[fd]['response'])
        loopone.update_handler(fd, ioloop.IOLoop.READ)
    elif event & ioloop.IOLoop.ERROR:
        print 'error connection detected!'
        loopone.remove_handler(fd)
        del clients[fd]

global clients,wninum,loc,mess_ids
clients = {}
mess_ids = {} #keep mess_id that already inserted, in case duplicated
wninum=0
from threading import Lock
loc = Lock()

class Connection(object):
    #clients = set()
    #clients = {}
    def __init__(self, stream, address):
        #Connection.clients.add(self)
        #Connection.clients[stream.fileno()] = self
        #self._response="content-length: 4\r\nshit\r\n"
        self._stream = stream
        stream.socket.setblocking(0)
        stream.socket.setsockopt(socket.IPPROTO_TCP, socket.TCP_NODELAY, 1)
        stream.socket.setsockopt(socket.SOL_SOCKET,socket.SO_REUSEADDR,1)
        self._fd = stream.fileno()
        self._address = address
        self._stream.set_close_callback(self.on_close)
        self.read_message()
        self._response = 'default resp'
        #self.retry = 0
        #self.timer = Timer(settings.retry_interval,self.feedback_timeout_handle)
        self.io_loop = ioloop.IOLoop.instance()
        self.pd_msg = []
        self.queue = Queue()
        self.lock = Lock()
        self.sendno_messid={}
        if debug:
            #print "A new user has entered the chat room.", address
            print "One device connected:%s" % str(address)
 
 
    def read_message(self,sendno=None,mess_id=None):
        #self._stream.read_until('*#*', self.broadcast_messages)
        #tot=loopone.add_timeout(datetime.timedelta(seconds=10), stack_context.wrap(self.timeout_handle))
        #from threading import Timer
        #t = Timer(10,self.timeout_handle)
        #t.start()
        if self._stream._read_callback == None:
            self._stream.read_until_regex('.*?\*[#&%]\*|sendno(.+)\*@\*', partial(self.send_message,mess_id,sendno))
        #self._stream.read_until_regex('sendno%s\*@\*'%sendno, partial(self.feed_ok,mess_id))
        #print 'shit'
        
        #self._stream.read_until_regex('.*', self.send_message)
        #loopone.remove_timeout(tot)
        #t.cancel()
    def read_message_bak(self):
        #self._stream.read_until('*#*', self.broadcast_messages)
        #tot=loopone.add_timeout(datetime.timedelta(seconds=10), stack_context.wrap(self.timeout_handle))
        #from threading import Timer
        #t = Timer(10,self.timeout_handle)
        #t.start()
        self._stream.read_until_regex('.*\*[#&%]\*', self.send_message)
        #self._stream.read_until_regex('sendno%s\*@\*'%sendno, partial(self.feed_ok,mess_id))
        #print 'shit'
        
        #self._stream.read_until_regex('.*', self.send_message)
        #loopone.remove_timeout(tot)
        #t.cancel()
 
    def broadcast_messages(self, num=None,data=None):
        #print "User said:", data[:-1], self._address
        #data = self._response if data is None else data
        #counter = len(Connection.clients) if num is None else num
        global start
        start = time.time()
        with open('/tmp/server.log','w') as f:
            pass
        #if debug:
        print 'Begin broadcast, currently has %s clients' % len(clients)
        if num is None:
            counter = len(clients)
            for conn in clients.itervalues():
                result = conn._response if data is None else data
                if debug:
                    print 'data is ' , result
                conn.write_to_client(result)
        else:
            counter = num
            x = 0
            for conn in clients.itervalues():
                if x >=counter:
                    break
                result = conn._response if data is None else data
                conn.write_to_client(result)
                x += 1
        #end = time.time()
        #print 'Finish broadcasting to %s clients within %s seconds' % (counter,int(end-start))
        #self.read_message()
    def broadcase_random(self,num=None):
        self.broadcast_messages(num=num)
    
    def write_to_client(self,data):
        self._stream.write(data,self.counton)
    
    def counton(self):
        global wninum
        global loc
        with open('/tmp/server.log','a') as f:
            f.write('write %s to %s\n' % (self._response,str(self._address)))
        loc.acquire()
        wninum += 1
        loc.release()
        #sys.stdout.write('%s clients sent!\r\n' % wninum)
        print '%s clients sent!\r\n' % wninum
        if wninum == len(clients):
            end = time.time()
            print 'Finish broadcasting to %s clients within %s seconds' % (wninum,int(end-start))
            wninum = 0 
 
    def wait_feedback_tmp(self,sendno,mess_id):
        #def wait_feedback(self):
        #self.lock.acquire()
        #self._stream.read_until_regex('.*', self.feed_ok)
        #self._stream.read_until_regex('sendno%s\*@\*'%sendno, lambda data: self.feed_ok(mess_id))
        self._stream.read_until_regex('sendno%s\*@\*'%sendno, partial(self.feed_ok,mess_id))
        
        #self._stream.read_until_regex('sendno:%s\*@\*'%sendno, functools.partial(ioloop.IOLoop.instance().add_callback, self.feed_ok))
    
    def send_message(self, mess_id,sendno,data):
        #self._stream.write(data)
        #for i in xrange(4):
            #time.sleep(5)
        #if data.strip().endswith('*#*'):
        #if re.search('id:appkey(.+)device(.+)\*#\*',data) != None:
        if re.search('{.+}\*#\*',data) != None:
            """
            print 'write data to ',self._address
            self._stream.write(self._response)
            """
            #self._devicetoken = re.search('id:(.+)\*#\*',data).group(1)
            #self.app_key,self._devicetoken = re.search('id:appkey(.+)device(.+)\*#\*',data).groups()
            try:
                tmp_str = re.search('({.+})\*#\*',data).groups()[0]
                json_obj = json.loads(tmp_str)
            except:
                exctrace('ADPNS','1','Parse json endswith *#* failed',logger,'Json loads *#* string failed','Json loads *#* detail: origin data is %s;groups zero is %s' % (data,tmp_str))
                return
            if utils.checkjsonkey(['appkey','device','action'],json_obj):
                self.app_key = json_obj['appkey']
                self._devicetoken = json_obj['device']
                self.status = None
                
                clients[self._devicetoken]=self
                #self._response = json.dumps(eval(msg_format % ('*'*67+'*#*',self._devicetoken)))
                self._response = msg_format % ('*'*67+'*#*',self._devicetoken)
                ##tmp_usr = session.query(Device).filter_by(devicetoken=self._devicetoken).first()
                ##if tmp_usr:
                ##    logger.log(30,'Device %s duplicated..' % self._devicetoken)
                ##else:
                ##    usr = Device(self._devicetoken)
                ##    session.add(usr)
                ##    session.commit()
                ##db_logger.log(20,'Add device %s' % self._devicetoken)
                if debug:
                    print self
                    print 'current clients number is : %s' % str(len(clients))
                            
                try:
                    #res = connection_writer.dbquery(whereclause=and_(connection_writer._table.c.app_key==self.app_key,connection_writer._table.c.device_token==self._devicetoken))
                    res = session.execute(connection_writer._table.select().where(connection_writer._table.c.app_key==self.app_key).where(connection_writer._table.c.device_token==self._devicetoken))
                except Exception,e:
                    #dba_logger.log(40,'Exception when dbwriter:%s' % str(e))
                    #dba_logger.log(20,'Exception detail:%s' % str(kwargs))
                    exctrace('db','1','Error happened when querying db',dba_logger,'Exception when query session_details:%s' % str(e),'Exception detail:appkey is %s,devicetoken is %s' % (self.app_key,self._devicetoken))
                    self.read_message()
                    return
                    #session.rollback()
                if res.first() is None:
                    if json_obj['action'] == 'reg':
                        connection_writer.dbwrite(app_key=self.app_key,device_token=self._devicetoken)
                        self.status = '0'
                        
                    else:
                        logger.log(30,'Connection action %s but no existing record for dbwrite' % json_obj['action'])
                        self._stream.close()
                        return 
                else:
                    if json_obj['action'] =='reg':
                        self.status = '0'
                        tmptime = datetime.datetime.now()
                        connection_writer.dbupdate(whereclause=and_(connection_writer._table.c.app_key==self.app_key,connection_writer._table.c.device_token==self._devicetoken),create_time=tmptime,end_time=tmptime,session_status=self.status)
                    elif json_obj['action'] == 'unreg':
                        self.status = '1'
                        #tmptime = datetime.datetime.now()
                        connection_writer.dbupdate(whereclause=and_(connection_writer._table.c.app_key==self.app_key,connection_writer._table.c.device_token==self._devicetoken),session_status=self.status)
                    else:
                        self.status = None
                    if self.status is None:
                        logger.log(30,'Invalid connection action %s for dbupdate' % json_obj['action'])
                        return
                    
            elif utils.checkjsonkey(['module','type','message'],json_obj):
                try:
                    #format = '%Y-%m-%d %H:%M:%S,%f'
                    tmp_time = datetime.datetime.strptime(json_obj['time'], '%Y-%m-%d %H:%M:%S')
                except:
                    tmp_time = datetime.datetime.now()
                ExceptionHandler.logException(json_obj['module'],json_obj['message'],json_obj['type'],tmp_time)
            else:
                logger.log(30,'Invalid json string with *#* received')
                if settings.deviceserver_log_debug:
                    logger.log(10,'Invalid json_obj:%s' % str(json_obj))
                return
            self.read_message()                     
        elif re.search('sendno(.+?)\*@\*',data) != None:
            sdn = re.search('sendno(.+?)\*@\*',data).group(1)
            #if sdn == sendno:
            self.read_message()
            if debug2:
                print 'mess_id is : %s,data is %s' % (mess_id,data)
            self.feed_ok(mess_id, data)
            
        elif data.strip().endswith('*&*'):
            #self._stream.close()
            #self.broadcase_random()
            pass
        elif data.strip().endswith('*%*'):
            #self._stream.close()
            self._stream.write('clients num:%s' % len(clients))
            self.read_message()
        else:
            pass
            #self._stream.write(data)
            #self._stream.write(self._response)
    
    def send_message_bak(self, data):
        #self._stream.write(data)
        #for i in xrange(4):
            #time.sleep(5)
        #if data.strip().endswith('*#*'):
        #if re.search('id:appkey(.+)device(.+)\*#\*',data) != None:
        if re.search('{.+}\*#\*',data) != None:
            """
            print 'write data to ',self._address
            self._stream.write(self._response)
            """
            #self._devicetoken = re.search('id:(.+)\*#\*',data).group(1)
            #self.app_key,self._devicetoken = re.search('id:appkey(.+)device(.+)\*#\*',data).groups()
            try:
                tmp_str = re.search('({.+})\*#\*',data).groups()[0]
                json_obj = json.loads(tmp_str)
            except:
                exctrace('ADPNS','1','Parse json endswith *#* failed',logger,'Json loads *#* string failed','Json loads *#* detail: origin data is %s;groups zero is %s' % (data,tmp_str))
                return
            if utils.checkjsonkey(['appkey','device','action'],json_obj):
                self.app_key = json_obj['appkey']
                self._devicetoken = json_obj['device']
                self.status = None
                
                clients[self._devicetoken]=self
                #self._response = json.dumps(eval(msg_format % ('*'*67+'*#*',self._devicetoken)))
                self._response = msg_format % ('*'*67+'*#*',self._devicetoken)
                ##tmp_usr = session.query(Device).filter_by(devicetoken=self._devicetoken).first()
                ##if tmp_usr:
                ##    logger.log(30,'Device %s duplicated..' % self._devicetoken)
                ##else:
                ##    usr = Device(self._devicetoken)
                ##    session.add(usr)
                ##    session.commit()
                ##db_logger.log(20,'Add device %s' % self._devicetoken)
                if debug:
                    print self
                    print 'current clients number is : %s' % str(len(clients))
                            
                res = session.execute(connection_writer._table.select().where(connection_writer._table.c.app_key==self.app_key).where(connection_writer._table.c.device_token==self._devicetoken))
                if res.first() is None:
                    if json_obj['action'] == 'reg':
                        connection_writer.dbwrite(app_key=self.app_key,device_token=self._devicetoken)
                        self.status = '0'
                        
                    else:
                        logger.log(30,'Connection action %s but no existing record for dbwrite' % json_obj['action'])
                        self._stream.close()
                        return 
                else:
                    if json_obj['action'] =='reg':
                        self.status = '0'
                        tmptime = datetime.datetime.now()
                        connection_writer.dbupdate(whereclause=and_(connection_writer._table.c.app_key==self.app_key,connection_writer._table.c.device_token==self._devicetoken),create_time=tmptime,end_time=tmptime,session_status=self.status)
                    elif json_obj['action'] == 'unreg':
                        self.status = '1'
                        #tmptime = datetime.datetime.now()
                        connection_writer.dbupdate(whereclause=and_(connection_writer._table.c.app_key==self.app_key,connection_writer._table.c.device_token==self._devicetoken),session_status=self.status)
                    else:
                        self.status = None
                    if self.status is None:
                        logger.log(30,'Invalid connection action %s for dbupdate' % json_obj['action'])
                        return
                    
            elif utils.checkjsonkey(['module','type','message'],json_obj):
                try:
                    #format = '%Y-%m-%d %H:%M:%S,%f'
                    tmp_time = datetime.datetime.strptime(json_obj['time'], '%Y-%m-%d %H:%M:%S')
                except:
                    tmp_time = datetime.datetime.now()
                ExceptionHandler.logException(json_obj['module'],json_obj['message'],json_obj['type'],tmp_time)
            else:
                logger.log(30,'Invalid json string with *#* received')
                if settings.deviceserver_log_debug:
                    logger.log(10,'Invalid json_obj:%s' % str(json_obj))
                return
            self.read_message()                     

        elif data.strip().endswith('*&*'):
            #self._stream.close()
            #self.broadcase_random()
            pass
        elif data.strip().endswith('*%*'):
            #self._stream.close()
            self._stream.write('clients num:%s' % len(clients))
            self.read_message()
        else:
            pass
            #self._stream.write(data)
            #self._stream.write(self._response)
 
    def on_close(self):
        if settings.deviceserver_log_debug:
            logger.log(10,"Device %s has left the chat room." % str(self._address))
        if hasattr(self,'app_key') and hasattr(self,'_devicetoken'):
            tmptime = datetime.datetime.now()
            connection_writer.dbupdate(whereclause=and_(connection_writer._table.c.app_key==self.app_key,connection_writer._table.c.device_token==self._devicetoken),end_time=tmptime,session_status='1')
        """
        try:
            dev = session.query(Device).filter_by(devicetoken=self._devicetoken).one()
            session.delete(dev)
            session.commit()
        except NoResultFound,e:
            logger.log(30,'Trying delete but no entry found %s'%self._devicetoken)
        except MultipleResultsFound,e:
            logger.log(30,'Trying delete but multiple entries found %s'%self._devicetoken)
        except Exception,e:
            logger.log(30,'Trying delete device but exception found %s'%self._devicetoken)
        db_logger.log(20,'Delete device %s'% self._devicetoken)
        """
        #del Connection.clients[self._fd]
        try:
            if self._devicetoken in clients:
                del clients[self._devicetoken]
        except (KeyError,AttributeError),e:
            logger.log(40,'Exception on close:%s'% str(e))
        if debug2:
            print 'on_close,current clients is : %s' % str(clients)
            
    def addNewMsg(self,msg):
        self.queue.put(msg)
        if not hasattr(self,'hthread'):
            self.hthread = Thread(target=self.keepsending,name=self._devicetoken)
            self.hthread.start()
    
    def keepsending(self):
        while True:
            tmp_msg = self.queue.get()
            for k,v in tmp_msg.iteritems():
                self.writeToDevice(v,k)
    
    
    def writeToDevice(self,tmp_dict,sendno):
        self.lock.acquire()
        self.to_device = tmp_dict
        mess_context = json.dumps(tmp_dict['msg_content'])
        mess_id = hashlib.new('md5',mess_context).hexdigest()
        self.sendno_messid[str(sendno)]=mess_id
        if self.status != '0':
            messages_details_writer.dbwrite(mess_id=mess_id,device_token=self._devicetoken,mess_status='2')
            return 
        data = genMsgToDevice(self._devicetoken,tmp_dict)
        #self.timer = Timer(settings.retry_interval,self.feedback_timeout_handle)
        #self.timer.start()
        #self.timeouter = self.io_loop.add_timeout(datetime.timedelta(seconds=settings.retry_interval), lambda : self.feedback_timeout_handle(sendno)) 
        self.addTry(sendno)
        #self.addTimer(sendno)
        self.addTimer(sendno,mess_id)
        try:
            #if self.retry == 0:
            if self.getTry(sendno)==0:
                #print '****************',self.getTry(sendno)
                #self._stream.write(data,self.wait_feedback)
                self._stream.write(data,lambda : self.read_message(sendno, mess_id))
                
            else:
                self._stream.write(data)
        except StreamClosedError,e:
            logger.log(30,'When writing, stream closed to %s(%s)' % (str(self._address),self._devicetoken))
            #self.io_loop.remove_timeout(self.timeouter)
            self.lock.release()
            self.delTimer(sendno)
            self.delTry(sendno)
            
    def writeToDevice_bak(self,tmp_dict,sendno):
        self.lock.acquire()
        self.to_device = tmp_dict
        mess_context = json.dumps(tmp_dict['msg_content'])
        mess_id = hashlib.new('md5',mess_context).hexdigest()
        if self.status != '0':
            messages_details_writer.dbwrite(mess_id=mess_id,device_token=self._devicetoken,mess_status='2')
            return 
        data = genMsgToDevice(self._devicetoken,tmp_dict)
        #self.timer = Timer(settings.retry_interval,self.feedback_timeout_handle)
        #self.timer.start()
        #self.timeouter = self.io_loop.add_timeout(datetime.timedelta(seconds=settings.retry_interval), lambda : self.feedback_timeout_handle(sendno)) 
        self.addTry(sendno)
        #self.addTimer(sendno)
        self.addTimer(sendno,mess_id)
        try:
            #if self.retry == 0:
            if self.getTry(sendno)==0:
                #print '****************',self.getTry(sendno)
                #self._stream.write(data,self.wait_feedback)
                self._stream.write(data,lambda : self.wait_feedback(sendno,mess_id))
                
            else:
                self._stream.write(data)
        except StreamClosedError,e:
            logger.log(30,'When writing, stream closed to %s(%s)' % (str(self._address),self._devicetoken))
            #self.io_loop.remove_timeout(self.timeouter)
            self.lock.release()
            self.delTimer(sendno)
            self.delTry(sendno)
            
    def addTimer(self,sendno,mess_id):
        #tmp = 'timer'+sendno
        setattr(self,'timer%s'% sendno,self.io_loop.add_timeout(datetime.timedelta(seconds=settings.retry_interval), self.addtimeout(self.feedback_timeout_handle,sendno,mess_id)))
        #setattr(self,'timer%s'% sendno,self.addtimeout(self.io_loop.add_timeout,timedelta,sendno))
    
    def addtimeout(self,callback,sendno,mess_id):
        return lambda : callback(sendno,mess_id)
    
    def delTimer(self,sendno):
        self.io_loop.remove_timeout(getattr(self,'timer%s'%sendno))
        
    def addTry(self,sendno):
        if not hasattr(self,'retry%s'%sendno):
            setattr(self,'retry%s'%sendno,0)
    
    def getTry(self,sendno):
        return getattr(self,'retry%s'%sendno)
    
    def incrTry(self,sendno):
        tmp = getattr(self,'retry%s'%sendno)
        tmp += 1
        setattr(self,'retry%s'%sendno,tmp)
    
    def resetTry(self,sendno):
        #tmp = getattr(self,'retry%s'%sendno)
        #tmp = 0
        self.addTry(sendno)
    
    def delTry(self,sendno):
        delattr(self,'retry%s'%sendno)
    
    
    def write_cb(self):
        self.read_feedback()
        #self.timer.cancel()

    def wait_feedback(self,sendno,mess_id):
        #def wait_feedback(self):
        #self.lock.acquire()
        #self._stream.read_until_regex('.*', self.feed_ok)
        #self._stream.read_until_regex('sendno%s\*@\*'%sendno, lambda data: self.feed_ok(mess_id))
        self._stream.read_until_regex('sendno%s\*@\*'%sendno, partial(self.feed_ok,mess_id))
        
        #self._stream.read_until_regex('sendno:%s\*@\*'%sendno, functools.partial(ioloop.IOLoop.instance().add_callback, self.feed_ok))
    
    def feed_ok(self,mess_id,data):
        #print '***********',data
        sdn = re.search('sendno(.+?)\*@\*',data).group(1)
        #wni: sometimes mess_id is None from send_message, so, work around here, dig later on
        try:
            mess_id = self.sendno_messid.pop(sdn)
        except KerError:
            logger.log(40,'Failed find mess_id via sdn. appkey:%s;devicetoken:%s, just set mess_id to None' % (self.app_key,self._devicetoken))
            mess_id = None
        messages_details_writer.dbwrite(mess_id=mess_id,device_token=self._devicetoken,mess_status='0')
        if settings.deviceserver_log_debug:
            logger.log(10,'Received confirm from %s'%str(self._address))
        
        #self.rmPendMsg(sdn)
        #self.pd_msg.pop(sdn,None)
        #self.timer.cancel()
        #self.io_loop.remove_timeout(self.timeouter)
        self.delTimer(sdn)
        self.delTry(sdn)
        self.lock.release()
    
    def feed_ok_bak(self,mess_id,data):
        messages_details_writer.dbwrite(mess_id=mess_id,device_token=self._devicetoken,mess_status='0')
        def final_ok(data):
            #print '***********',data
            if debug:
                logger.log(10,'Received confirm from %s'%str(self._address))
            sdn = re.search('sendno(.+)\*@\*',data).group(1)
            #self.rmPendMsg(sdn)
            #self.pd_msg.pop(sdn,None)
            #self.timer.cancel()
            #self.io_loop.remove_timeout(self.timeouter)
            self.delTimer(sdn)
            self.delTry(sdn)
            self.lock.release()
        final_ok(data)
    
    def rmPendMsg(self,sendno):
        for x in self.pd_msg:
            if x['sendno'] == sendno:
                self.pd_msg.remove(x)
    
    def feedback_timeout_handle(self,sendno,mess_id):
        if self.getTry(sendno) < settings.retry_times:
        #if self.retry < settings.retry_times:
            self.incrTry(sendno)
            #self.retry += 1
            #logger.log(30,'Retry to %s No.%s' % (str(self._address),str(self.retry)))
            logger.log(30,'Retry to %s(%s) No.%s' % (str(self._address),sendno,str(self.getTry(sendno))))
            try:
                self.lock.release()
            except:
                pass
            #self.timer.cancel()
            self.writeToDevice(self.to_device,sendno)
        else:
            messages_details_writer.dbwrite(mess_id=mess_id,device_token=self._devicetoken,mess_status='1')
            ExceptionHandler.logException('ADPNS','Pushing to %s(%s) exceeding max times' % (self.app_key,self._devicetoken),'0',datetime.datetime.now())
            logger.log(30,'Sending message to %s(%s) exceeds max retries.Message:%s'%(str(self._address),sendno,str(self.to_device)))
            self.resetTry(sendno)
            #self.retry = 0
            #self._stream._read_callback = None
            self.lock.release()
        """
        if self.retry < settings.retry_times:
            self.retry += 1
            logger.log(30,'Retry to %s No.%s' % (str(self._address),str(self.retry)))
            #self.timer.cancel()
            self.writeToDevice(self.to_device)
        else:
            logger.log(40,'Sending message to %s exceeds max retries.Message:%s'%(str(self._address),str(self.to_device)))
            self.retry=0
       """
    
    def __str__(self):
        return 'Connection object,appkey:%s,devicetoken:%s,response:%s,address:%s' % (self.app_key,self._devicetoken,self._response,str(self._address))
"""
class Consumer(threading.Thread):
def __init__(self, threadname, queue):
threading.Thread.__init__(self, name = threadname)
self.sharedata = queue
def run(self):
for i in range(20):
print self.getName(),'got a value:',self.sharedata.get()
time.sleep(random.randrange(10)/10.0)
print self.getName(),'Finished'
"""
      
class MonitorTCPServer(TCPServer):
    def handle_stream(self, stream, address):
        #MtaskConnection(stream,address)
        if settings.deviceserver_log_debug:
            logger.log(10,'Got connection from %s' % str(address)) 
            #logger.log(10,'Got connection from %s to local %s' % (str(address),stream.socket.getsockname()))      
        
        Connection(stream, address)
        #stream.socket.setblocking(0)
        #stream.socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1) 
        #loopone.add_handler(stream.fileno(), response, ioloop.IOLoop.READ)
        #stream.read_until('*#*',self.cbk1)
        #stream.write(clients[stream.fileno()]['response'])
        #print "connection num is:", len(Connection.clients)
        
    """
    def cbk1(self,data):
        print 'received %s from %s' % (data,'shit')
        self.stream.write(clients[self.stream.fileno()]['response'])
      """  
        #stream.write(clients[stream.fileno()]['response'])
        #print 'sent data to',address    
def startHttpConn_router_dealer():
    """
    {'msg_content': {u'message': u'{"command":true}'}, 'targets': [u'b0_aa_36_1c_dd_37'], 'msg_type': '2'}
    msg_format = '{"msg":\"%s\","id":%s,"flag":"*#*"}'
    """
    context = zmq.Context() 
    responser = context.socket(zmq.DEALER) 
    responser.setsockopt(zmq.IDENTITY, b'A')
    #responser.setsockopt(zmq.LINGER,0)
    responser.bind("tcp://%s:%s" % (settings.ADPNS_ip,settings.for_http_port)) 
    logger.log(20,'httpMQ started...')
     
    while True: 
        # Wait for next request from client 
        message = responser.recv_json() 
        responser.send_json({"1":"1"})
        #ident,message = responser.recv_multipart()
        #message = responser.recv()
        #print repr(message)
        if debug or settings.deviceserver_log_debug:
            logger.log(10,"Received PSG request: %s " % str(message)) 
        # Send reply back to client 
        #responser.send("*#*")
        # Dosome 'work'
        #time.sleep (1) # Do some 'work'
        pushToDevice(json.dumps(message))

def startHttpConn():
    """
    {'msg_content': {u'message': u'{"command":true}'}, 'targets': [u'b0_aa_36_1c_dd_37'], 'msg_type': '2'}
    msg_format = '{"msg":\"%s\","id":%s,"flag":"*#*"}'
    """
    context = zmq.Context() 
    responser = context.socket(zmq.PULL) 
    #responser.setsockopt(zmq.LINGER,0)
    responser.bind("tcp://%s:%s" % (settings.PSG_ip,settings.for_http_port)) 
    logger.log(20,'httpMQ started...')
     
    while True: 
        # Wait for next request from client 
        message = responser.recv_json() 
        if debug or settings.deviceserver_log_debug:
            logger.log(10,"Received PSG request: %s " % str(message)) 
        # Send reply back to client 
        #responser.send("*#*")
        # Dosome 'work'
        #time.sleep (1) # Do some 'work'
        pushToDevice(json.dumps(message))

def startHttpConn_bak():
    """
    {'msg_content': {u'message': u'{"command":true}'}, 'targets': [u'b0_aa_36_1c_dd_37'], 'msg_type': '2'}
    msg_format = '{"msg":\"%s\","id":%s,"flag":"*#*"}'
    """
    context = zmq.Context() 
    responser = context.socket(zmq.REP) 
    #responser.setsockopt(zmq.LINGER,0)
    responser.bind("tcp://*:%s"%settings.for_http_port) 
    logger.log(20,'httpMQ started...')
     
    while True: 
        # Wait for next request from client 
        message = responser.recv() 
        if debug:
            logger.log(10,"Received PSG request: %s " % message) 
        # Send reply back to client 
        responser.send("*#*")
        # Dosome 'work'
        #time.sleep (1) # Do some 'work'
        pushToDevice(message)        
        
def pushToDevice(message):
    msg_dict = json.loads(message)
    #mess_id = uuid.uuid4()
    
    try:
        mess_context = json.dumps(msg_dict['msg_content'])
    except:
        exctrace('ADPNS','1','Dump msg_content failed',logger,'pushToDevice dumps msg_content failed','msg_dict is %s' % str(msg_dict))
        return
    mess_id = hashlib.new('md5',mess_context).hexdigest()
    if mess_id not in mess_ids:
        messages_writer.dbwrite(mess_id=mess_id, mess_context=mess_context)
        mess_ids[mess_id] = '0'
    tmp_dict = {}
    targets = None
    for k,v in msg_dict.iteritems():
        if k != 'targets':
            tmp_dict[k]=v
        else:
            targets = v
    if targets is None:
        logger.log(40,'Failed to get targets from %s' % message)
        return
    for token in targets:
        try:
            device_conn = clients[token]
        except:
            logger.log(40,'Cannot find device via token %s' % token)
            if debug or settings.deviceserver_log_debug:
                logger.log(10,'Current clients:%s' % ';'.join(clients.iterkeys()))
            continue
        ##fin_msg = genMsgToDevice(token,tmp_dict)
        #if tmp_dict['sendno'] in device_conn.pd_msg:
        if checkinlist(tmp_dict['sendno'],device_conn.pd_msg):
            logger.log(30,'Same sendno detected in pending msg of token %s!Just discard this message' % token)
            continue
        #device_conn.pd_msg[tmp_dict['sendno']] = fin_msg
        #device_conn.addNewMsg({'sendno' : fin_msg})
        #device_conn.pd_msg.append({'sendno' : fin_msg})
        device_conn.writeToDevice(tmp_dict,tmp_dict['sendno'])

def checkinlist(sendno,lst):
    for x in lst:
        if x['sendno'] == sendno:
            return True        

def genMsgToDevice(id,msg_dict):
    tmp_msg = msg_format_http % str(id)
    tmp_str = json.dumps(msg_dict)
    fin_str = tmp_str[:-1] + ',' + tmp_msg[1:]
    return fin_str
    

def main():
    global loopone
    """
    sockets = netutil.bind_sockets(port,backlog=4000)
    sockets2 = netutil.bind_sockets(port2,backlog=4000)
    for sock in sockets+sockets2:
        sock.setblocking(0)
        sock.setsockopt(socket.IPPROTO_TCP, socket.TCP_NODELAY, 1)
    process.fork_processes(0)
    server = MonitorTCPServer()
    server.add_sockets(sockets+sockets2)
    print "Listening on port", port
    
    """
    logger.log(20,"Server start ......")    
    server = MonitorTCPServer()    
    server.listen(settings.for_device_port)    
    http_thd = Thread(target=startHttpConn,name='httpwaiter')
    http_thd.start()
    loopone = ioloop.IOLoop.instance()
    loopone.start()
    
 
if __name__ == '__main__':
    from libs import kernal
    kernal.chkernal()
    main()