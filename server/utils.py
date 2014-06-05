#!/usr/bin/env python

import logging
import logging.handlers
import settings

class Logger(object):
    @staticmethod
    def createLogger(name=settings.overroll_name,level=settings.overroll_level,fd=settings.overroll_file):
        logger = logging.getLogger(name)
        logger.setLevel(level)
        #handler = logging.FileHandler(fd)
        handler = logging.handlers.RotatingFileHandler(fd,'a',1048576*2,10)
        handler.setLevel(level)
        
        formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
        handler.setFormatter(formatter)
        logger.addHandler(handler)
        logger.propagate = settings.to_print
        return logger
    
def checkjsonkey(check_list,jsonobj):
    for item in check_list:
        if item not in jsonobj:
            return False
    return True

#global_logger = Logger.createLogger()
    