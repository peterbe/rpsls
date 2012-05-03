import datetime
import tornado.options
import tornado.escape
from tornado import web, ioloop
from sockjs.tornado import SockJSRouter, SockJSConnection
from tornado.options import define, options
import settings
import cookies


define("debug", default=False, help="run in debug mode", type=bool)
define("port", default=9999, help="run on the given port", type=int)


class PlayConnection(SockJSConnection):
    _connected = set()
    _waiting = []
    _groups = []

    def on_open(self, request):
        cookie_parser = cookies.CookieParser(request)
        username = cookie_parser.get_secure_cookie('user')
        self._connected.add(self)

        if username:
            self._on_register(username)

    def on_message(self, msg):
        try:
            data = tornado.escape.json_decode(msg)
        except ValueError:
            data = msg
        if data.get('register'):
            self._on_register(data.get('register'))
        else:
            print "DATA", repr(data)
            data['date'] = datetime.datetime.now().strftime('%H:%M:%S')
            #self.broadcast(self._connected, data)

    def on_close(self):
        # Remove client from the clients list and broadcast leave message
        self._connected.remove(self)
        #self.broadcast(self.participants, "Someone left.")

    def _on_register(self, username):
        self.nick = username
        self.send({'registered': self.nick})
        while self._waiting:
            opponent = self._waiting.pop()
            if opponent.is_closed:
                continue
            self.send({'status': "playing against " + opponent.nick})
            opponent.send({'status': "playing against " + self.nick})
            break

        else:
            self._waiting.append(self)
            self.send({'status': 'Waiting', 'color': 'orange'})




if __name__ == '__main__':
    tornado.options.parse_command_line()
    EchoRouter = SockJSRouter(PlayConnection, '/play')
    app_settings = dict(
      debug=options.debug,
      cookie_secret=settings.COOKIE_SECRET,
    )
    app = web.Application(EchoRouter.urls, **app_settings)
    app.listen(options.port)
    print "Running sock app on port", options.port
    ioloop.IOLoop.instance().start()
