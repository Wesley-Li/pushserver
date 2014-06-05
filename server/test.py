#!/usr/bin/env python
#coding:utf-8

#from sqlalchemy.orm import sessionmaker
#Session = sessionmaker(bind=engine)

##from exception_handler import ExceptionHandler
##from datetime import datetime

##ExceptionHandler.logException('中国','PSG:level 0 exception','1',datetime.now())
##from libs.dbwriter import messages_writer

##import uuid
#messages_writer.dbwrite(mess_id=str(uuid.uuid4()), mess_context='nipen'*40)
import urllib,urllib2,json,sys,hashlib
counter = 0
range1 = sys.argv[1]
low,high = range1.split('-')
data = '{"sendno": %s,"app_key":"e32c72bab0e4d8e225318f98","receiver_type":3,"receiver_value":"%s","verification_code":"%s","msg_type":2,"msg_content":{"message":{\"command\":true}},"platform":"android"}'
#mydata = urllib.urlencode(data)

for i in xrange(int(low),int(high)+1):

    #5. Call urllib2.urlopen() and pass the data from urlencode() as the second argument, like this:
    tmp = str(i) + '3' + str(i) + 'CHUANGYITUISONG007'
    md5_string = hashlib.new('md5',tmp).hexdigest()
    tmpdata = data % (str(i),str(i),md5_string)
    #print tmpdata
    res = urllib2.urlopen('http://127.0.0.1/push', json.dumps(json.loads(tmpdata)))
    ret = json.loads(res.read())
    if ret['errcode']==0:
        counter = counter + 1
    else:
        print ret
    
print 'Success:%s' % counter
