#!/usr/bin/env python
#coding:utf-8
import logging
#import utils

engine_echo = False

pool_rec = True
pool_recycle_time = 7200


deviceserver_debug = True
deviceserver_log_debug = True
psg_log_debug = True
ADPNS_with_db = True

msg_limit = 220
#logger related
overroll_level = logging.DEBUG
overroll_name = 'general'
overroll_file = 'general.log'


err_mapping = {0:'Success',10:'Internal error',1001:'Only support HTTP POST',1002:'Lack of parameters',
               1003:'Invalid param value',1004:'Verification failed',1005:'Body too long',1006:'Username or password error',
            1007:'Invalid receiver_value',1008:'Invalid app key',1010:'Invalid msg content',1011:'No matching target',
            1013:'Invalid content type',
               }

db_tbs = { 'connection':'sessions_details','message':'messages','message_detail':'messages_details'}
#messages_writer = DBWriter('messages')
#connection_writer = DBWriter('sessions_details')
#messages_details_writer = DBWriter('messages_details')

# device server settings
for_device_port = 21567
for_http_port = 21568

to_print = False

