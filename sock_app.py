import datetime
import tornado.options
import tornado.escape
from tornado import web, ioloop
from sockjs.tornado import SockJSRouter, SockJSConnection
from tornado.options import define, options

define("debug", default=False, help="run in debug mode", type=bool)
define("port", default=9999, help="run on the given port", type=int)


class PlayConnection(SockJSConnection):
    _connected = set()
    _waiting = []
    _groups = []

    def on_open(self, *args, **kwargs):
        #print "ARGS", args
        #print "KWARGS", kwargs
        self._connected.add(self)
#        if _waiting:
#            him = _waiting.pop()
#            group = (self, him)
#            self._groups.append(group)
#            self.start_group(group)
#        else:
#            self._waiting.append(self)

    def on_message(self, msg):
        try:
            data = tornado.escape.json_decode(msg)
        except ValueError:
            data = msg
        if data.get('register'):
            self.nick = data.get('register')
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
        else:
            print "DATA", repr(data)
            data['date'] = datetime.datetime.now().strftime('%H:%M:%S')
            self.broadcast(self._connected, data)

    def on_close(self):
        # Remove client from the clients list and broadcast leave message
        self._connected.remove(self)
        self.broadcast(self.participants, "Someone left.")



if __name__ == '__main__':
    tornado.options.parse_command_line()
    EchoRouter = SockJSRouter(PlayConnection, '/play')
    app_settings = dict(
      debug=options.debug
    )
    app = web.Application(EchoRouter.urls, **app_settings)
    app.listen(options.port)
    print "Running sock app on port", options.port
    ioloop.IOLoop.instance().start()
