#import tornado
#from sqlalchemy.orm import scoped_session, sessionmaker
#from models import *  # import the engine to bind

from tornado.httpserver import HTTPServer
from tornado.ioloop import IOLoop
import tornado.web
import json,hashlib
import utils
import db
from models import App
import settings
import zmq
import traceback
#from settings import apps,err_mapping,msg_limit

logger = utils.Logger.createLogger('httpserv',fd='./logs/httpserv.log')
rep_format = '{"errcode":%s,"errmsg":\"%s\","msg_id":0}'

class Application(tornado.web.Application):
    def __init__(self):
        handlers = [
            (r"/push", MainHandler),
        ]
        settings = dict(
            cookie_secret="some_long_secret_and_other_settins"
        )
        tornado.web.Application.__init__(self, handlers, **settings)
        # Have one global connection.
        self.db = db.session

class BaseHandler(tornado.web.RequestHandler):
    @property
    def db(self):
        return self.application.db

    def get_current_user(self):
        user_id = self.get_secure_cookie("user")
        if not user_id: return None
        return self.db.query(User).get(user_id)

class MainHandler(tornado.web.RequestHandler):
    """
    &sendno=524998753&app_key=e32c72bab0e4d8e225318f98&receiver_type=3&receiver_value=b0_aa_36_1c_dd_37
    &verification_code=f0c2f5a6996b877e72acdc7d472544ca&msg_type=2
    &msg_content={"message":"{\"command\":true}"}&platform=android
    """
    def get(self):
        #usr = self.application.db.query(App).first()
        #self.write("Hello, world")
        #self.write(str(usr))
        #self.write(rep_format % (1001,err_mapping[1001]))
        self.response(1001)
        ##self.write(repr(self.request))
        if settings.psg_log_debug:
            logger.log(30,'Get HTTP GET request from %s, just reject!' % self.request.remote_ip)
        
    def post(self):
        """
        name = self.get_argument('name1','name_unkown')
        if name != 'name_unkown':
            self.write('your name %s' % name)
        self.write(json.dumps(json.loads(self.request.body)))
        """
        self.parseBody()
    def parseBody(self):
        try:
            msg = json.loads(self.request.body)
            sendno = str(msg['sendno'])
            app_key = msg['app_key']
            receiver_type = str(msg['receiver_type'])
            receiver_value = msg['receiver_value']
            verification_code = msg['verification_code']
            msg_type = str(msg['msg_type'])
            msg_content = msg['msg_content']
            platform = msg['platform']
            self.validate(app_key, sendno, receiver_type, receiver_value, verification_code,msg_content)
            if self._finished:
                return
            targets = receiver_value.split(',')
            msg_dict = {}
            msg_dict['targets'] = targets
            msg_dict['msg_type'] = msg_type
            msg_dict['msg_content'] = msg_content
            msg_dict['sendno'] = sendno
            #self.sendPushSig(settings.device_server_ip,settings.for_http_port,msg_dict)
            if not self._finished:
                self.response(0)
                self.finish()
            self.sendPushSig(settings.device_server_ip,settings.for_http_port,msg_dict)
        except Exception,e:
            traceback.print_exc()
            logger.log(40,'Exception(parseBody):%s'% str(e))
            logger.log(30,'request body: %s'% str(self.request.body))
            self.response(1002)
            self.finish()
    def validate(self,app_key,sendno, receiver_type, receiver_value, verification_code,msg_content):
        security = None
        for app in settings.apps:
            if app['app_key'] == app_key:
                security = app['master_secret']
        if security is None:
            logger.log(40,'Cannot find master secret via app key:%s' % app_key) 
            self.response(1008)
            self.finish()
            return
        if (type(receiver_value) != type('1') and type(receiver_value)!=type(u'1')) or len(receiver_value)==0:
            self.response(1007)
            self.finish()
            return
        tmp = sendno + receiver_type + receiver_value + security
        md5_string = hashlib.new('md5',tmp).hexdigest()
        if md5_string != verification_code:
            self.response(1004)
            self.finish()
            return
        if len(str(msg_content)) > settings.msg_limit:
            self.response(1005)
            self.finish()
            return 
    
    def response(self,errcode):
        self.write(rep_format % (errcode,settings.err_mapping[errcode]))
    
    def sendPushSig_router_dealer(self,deviceserver,port,msg_dict):
        context = zmq.Context()
        requester = context.socket(zmq.ROUTER);
        requester.setsockopt(zmq.LINGER,0)
        requester.connect("tcp://%s:%s" % (deviceserver,port))
        import time
        time.sleep(0.5)
        #requester.send("Hello");
        #requester.send_json(msg_dict) 
        requester.send_multipart([b'A',json.dumps(msg_dict)])
        ident, mess = requester.recv_multipart()
        if "1" in tmpobj:
            print 'success'
        #print mess
        #requester.send_multipart()
        #poller = zmq.Poller()  
        #poller.register(requester, zmq.POLLIN)  
        #if poller.poll(1000): # 10s timeout in milliseconds  
        #    strs = requester.recv()
        #else:  
            #raise IOError("Timeout processing auth request")
        #    pass
        #print 'Client received: %s' % strs
        logger.log(20,'Send to %s:%s;msg:%s' % (str(deviceserver),str(port),str(msg_dict)))
        
        requester.close()
        context.term()
    
    def sendPushSig(self,deviceserver,port,msg_dict):
        context = zmq.Context()
        requester = context.socket(zmq.PUSH);
        #requester.setsockopt(zmq.LINGER,0)
        requester.connect("tcp://%s:%s" % (deviceserver,port))
        #requester.send("Hello");
        requester.send_json(msg_dict) 
        #poller = zmq.Poller()  
        #poller.register(requester, zmq.POLLIN)  
        #if poller.poll(1000): # 10s timeout in milliseconds  
        #    strs = requester.recv()
        #else:  
            #raise IOError("Timeout processing auth request")
        #    pass
        #print 'Client received: %s' % strs
        logger.log(20,'Send to %s:%s;msg:%s' % (str(deviceserver),str(port),str(msg_dict)))
        
        requester.close()
        context.term()
    
    def sendPushSig_req_rep(self,deviceserver,port,msg_dict):
        context = zmq.Context()
        requester = context.socket(zmq.REQ);
        requester.setsockopt(zmq.LINGER,0)
        requester.connect( "tcp://%s:%s" % (deviceserver,port) )
        #requester.send("Hello");
        requester.send(json.dumps(msg_dict)) 
        poller = zmq.Poller()  
        poller.register(requester, zmq.POLLIN)  
        if poller.poll(1000): # 10s timeout in milliseconds  
            strs = requester.recv()
        else:  
            #raise IOError("Timeout processing auth request")
            pass
        #print 'Client received: %s' % strs
        logger.log(20,'Send to %s:%s;msg:%s' % (str(deviceserver),str(port),str(msg_dict)))
        
        requester.close()
        context.term()
        

#application = tornado.web.Application([
#    (r"/", MainHandler),
#])
application = Application()

if __name__ == "__main__":
    
    from libs import kernal
    kernal.chkernal()
    
    http_server = tornado.httpserver.HTTPServer(application)
    http_server.bind(80)
    http_server.start()
    logger.log(20,'PSG started...')
    tornado.ioloop.IOLoop.instance().start()
    
    """
    sockets = tornado.netutil.bind_sockets(80)
    logger.log(20,'http server started...')
    tornado.process.fork_processes(0)
    server = HTTPServer(application)
    server.add_sockets(sockets)
    
    IOLoop.instance().start()
    """
    
    