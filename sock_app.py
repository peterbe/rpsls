import datetime
from collections import defaultdict
import tornado.options
import tornado.escape
from tornado import web, ioloop
from sockjs.tornado import SockJSRouter, SockJSConnection
from tornado.options import define, options
import redis.client
import settings
import cookies


define("debug", default=False, help="run in debug mode", type=bool)
define("port", default=9999, help="run on the given port", type=int)

def compare(mine, theirs):
    if mine == theirs:
        return 0
    if mine == 'rock':
        if theirs == 'scissor':
            return 1
    elif mine == 'paper':
        if theirs == 'rock':
            return 1
    elif mine == 'scissor':
        if theirs == 'paper':
            return 1
    return -1



class PlayConnection(SockJSConnection):
    _connected = set()
    _waiting = []
    _opponents = defaultdict(list)

    @property
    def redis(self):
        global _redis_connection
        if not _redis_connection:
            _redis_connection = redis.client.Redis(settings.REDIS_HOST,
                                                   settings.REDIS_PORT)
        return _redis_connection


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
        elif data.get('button'):
            self._on_button(data.get('button'))
        else:
            print "DATA", repr(data)
            data['date'] = datetime.datetime.now().strftime('%H:%M:%S')
            opponents = self._opponents.get(self.session, [])
            self.broadcast(opponents + [self], data)


    def on_close(self):
        print "Closing", self.session, getattr(self, 'nick', '*no nick*')
        opponent = self._opponents.get(self.session)
        if opponent:
            opponent.send({'status': self.nick + ' disconnected :(',
                           'color': 'red'})
            del self._opponents[opponent.session]
            del self._opponents[self.session]
        # Remove client from the clients list and broadcast leave message
        self._connected.remove(self)
        #self.broadcast(self.participants, "Someone left.")

    def _on_button(self, button):
        opponents = self._opponents[self.session]
        opponent = opponents[0]  # needs to get smarter
        if getattr(opponent, 'current_button', None):
            result = compare(button, opponent.current_button)
            if result == 1:
                self.redis.zincrby('wins', self.nick, 1)
                self.redis.zincrby('losses', opponent.nick, 1)
                self.redis.incr('%s:wins' % self.nick)
                self.redis.incr('%s:losses' % opponent.nick)
                your_news = {'won': 1}
                opponent_news = {'won': -1}
            elif result == -1:
                self.redis.zincrby('losses', self.nick, 1)
                self.redis.zincrby('wins', opponent.nick, 1)
                self.redis.incr('%s:losses' % self.nick)
                self.redis.incr('%s:wins' % opponent.nick)
                your_news = {'won': -1}
                opponent_news = {'won': 1}
            else:
                self.redis.zincrby('draws', self.nick, 1)
                self.redis.zincrby('draws', opponent.nick, 1)
                self.redis.incr('%s:draws' % self.nick)
                self.redis.incr('%s:draws' % opponent.nick)
                your_news = {'draw': True}
                opponent_news = {'draw': True}

            your_news['update_score'] = self._get_score(self.nick)
            self.send(your_news)
            opponent_news['update_score'] = self._get_score(opponent.nick)
            opponent.send(opponent_news)

            try:
                del self.current_button
            except AttributeError:
                pass
            try:
                del opponent.current_button
            except AttributeError:
                pass

        else:
            self.current_button = button
            opponent.send({'status': self.nick + ' has picked one',
                           'color': 'green'})

    def _on_register(self, username):
        self.nick = username
        self.send({'registered': self.nick})
        score = self._get_score(self.nick)
        self.send({'update_score': score})
        while self._waiting:
            opponent = self._waiting.pop()
            if opponent.is_closed:
                continue
            self._opponents[self.session].append(opponent)
            self._opponents[opponent.session].append(self)
            self.send({'status': "playing against " + opponent.nick,
                       'ready': True})
            opponent.send({'status': "playing against " + self.nick,
                           'ready': True})
            break

        else:
            self._waiting.append(self)
            self.send({'status': 'Waiting', 'color': 'orange'})

    def _get_score(self, username):
        data = {}
        data['wins'] = self.redis.get('%s:wins' % username) or 0
        data['draws'] = self.redis.get('%s:draws' % username) or 0
        data['losses'] = self.redis.get('%s:losses' % username) or 0
        return data


_redis_connection = None

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
