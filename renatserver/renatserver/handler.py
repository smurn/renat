# Copyright (C) 2014 Stefan C. Mueller

import datetime
import json

import tornado.web
import tornado.gen

class RecordIdHandler(tornado.web.RequestHandler):
    
    def get(self, record_id):
        self.render("put.html", record_id=record_id)

class RecordHandler(tornado.web.RequestHandler):
    
    MAX_TIMEOUT = 60
    
    @tornado.gen.coroutine
    def get(self, record_id, record_version):
        
        db = self.application.settings["db"]
        now = datetime.datetime.now()
        self.set_header("X-Request-From", self.request.remote_ip)
    
    
        timeout = int(self.get_argument("timeout", default="0"))
        timeout = max(timeout, 0)
        timeout = min(timeout, self.MAX_TIMEOUT)
        
        if record_version == "OLDEST":
            record_version = yield _timeout_helper(db.oldest_version, db.oldest_version_future, timeout, [record_id, now])
        
        if record_version == "JUNGEST":
            record_version = yield _timeout_helper(db.jungest_version, db.jungest_version_future, timeout, [record_id, now])
        
        if record_version is not None:
            record_version = int(record_version)
        
        if record_version is None:
            data = None
        else:
            data = yield _timeout_helper(db.get, db.get_future, timeout, [record_id, record_version, now])
        
        
        
        if data is None:
            self.send_error(404)
        else:
            response = {"record_id": record_id,
                         "record_version": record_version,
                         "value":data}
            self.finish(json.dumps(response, indent=4))
            
            
    def post(self, record_id, record_version):
        db = self.application.settings["db"]
        now = datetime.datetime.now()
        
        idepo = self.get_argument("idepo")
        data = self.get_argument("data")
        
        if record_version != "JUNGEST":
            raise ValueError("Can only post records as jungest.")
        
        record_version = db.put(record_id, idepo, data, now)
         
        response = {"record_id": record_id,
                     "record_version": record_version}
        self.finish(json.dumps(response, indent=4))
            
            
    def write_error(self, status_code, **kwargs):
        self.set_header("X-Request-From", self.request.remote_ip)
        tornado.web.RequestHandler.write_error(self, status_code, **kwargs)


@tornado.gen.coroutine   
def _timeout_helper(regular_func, future_func, timeout, args):
    if timeout > 0:
        future = future_func(*args)
        future = tornado.gen.with_timeout(timeout, future)
        try:
            retval = yield future
        except tornado.gen.TimeoutError:
            retval = None
    else:
        retval = regular_func(*args)
    raise tornado.gen.Return(retval)

