# Copyright (C) 2014 Stefan C. Mueller

import os.path
import inspect

import tornado.ioloop
import tornado.web

from renatserver import handler, db, asyncdb


template_path = os.path.join(
         os.path.dirname(
               os.path.abspath(
                  inspect.getfile(
                     inspect.currentframe()
                  )
               )
        ),
        "templates")


db = asyncdb.ASyncRecordDatabase(db.InMemoryRecordDatabase())

application = tornado.web.Application([
    (r"/rec/(?P<record_id>[0-9a-zA-Z_\-]+)/?", handler.RecordIdHandler),
    (r"/rec/(?P<record_id>[0-9a-zA-Z_\-]+)/(?P<record_version>\-?[A-Z0-9]+)", handler.RecordHandler)
], template_path=template_path, db=db)

def main():
    application.listen(8888)
    tornado.ioloop.IOLoop.instance().start()

if __name__ == '__main__':
    main()