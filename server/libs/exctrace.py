#!/usr/bin/env python
#coding: utf-8

import os,sys

server_path = os.path.join(os.path.dirname(os.path.abspath(__file__)),'..')
if server_path not in sys.path:
    sys.path.append(server_path)

from exception_handler import ExceptionHandler
from datetime import datetime

def exctrace(module,type,message,logger,exc_info,exc_trace,time=datetime.now()):
    #ExceptionHandler.logException('PSG','0','PSG:level 0 exception',datetime.now())
    ExceptionHandler.logException(module,type,message,time)
    logger.log(40,exc_info)
    logger.log(20,exc_trace)