import os
import tornado.httpserver
import tornado.ioloop
import tornado.web
from tornado.options import define, options

define("debug", default=False, help="run in debug mode", type=bool)
define("port", default=8000, help="run on the given port", type=int)


class HomeHandler(tornado.web.RequestHandler):
    def get(self):
        self.render('index.html')


class ManifestHandler(tornado.web.RequestHandler):
    def get(self):
        self.set_header('Content-Type', 'application/x-web-app-manifest+json')
        self.render('manifest.json')


def app():
    app_settings = dict(
      static_path=os.path.join(os.path.dirname(__file__), 'static'),
      template_path=os.path.join(os.path.dirname(__file__), 'templates'),
      debug=options.debug,

    )
    return tornado.web.Application([
        (r'/', HomeHandler),
        (r'/manifest.webapp', ManifestHandler),
    ], **app_settings)


if __name__ == '__main__':
    tornado.options.parse_command_line()
    app().listen(options.port)
    print 'Running on port', options.port
    tornado.ioloop.IOLoop.instance().start()
