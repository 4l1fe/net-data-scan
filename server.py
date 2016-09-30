import os
import sqlite3
import collections
import tornado.ioloop
import tornado.web
from tornado.options import define, options

define('port', default=8000)

NamedRow = collections.namedtuple('NamedRow', 'rowid packet')
def NamedRowFactory(cursor, row):
    return NamedRow(*row)

conn = sqlite3.connect('NDStore')
conn.row_factory = NamedRowFactory
cur = conn.cursor()


class MainHandler(tornado.web.RequestHandler):

    def get(self):
        cur.execute('''SELECT protocol, count(*)
                       FROM NDStore
                       GROUP BY protocol;''')
        self.render('admin.html', title='NDStore admin', packets=cur)


if __name__ == "__main__":
    application = tornado.web.Application([
        (r"/", MainHandler),
    ], debug=True,
       static_path=os.path.join(os.path.dirname(__file__), "static"))
    application.listen(options.port)
    tornado.ioloop.IOLoop.current().start()
