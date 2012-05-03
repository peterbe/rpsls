import Cookie
import time
import hmac
import hashlib
import base64
import logging
from tornado import escape
import settings


class CookieParser(object):
    """hackishly naive"""

    def __init__(self, request):
        self.request = request

    @property
    def cookies(self):
        """A dictionary of Cookie.Morsel objects."""
        if not hasattr(self, "_cookies"):
            self._cookies = self.request.cookies
            #self._cookies = Cookie.BaseCookie()
            #if "Cookie" in self.request.headers:
            #    try:
            #        self._cookies.load(
            #            escape.native_str(self.request.headers["Cookie"]))
            #    except:
            #        self.clear_all_cookies()
        return self._cookies

    def clear_all_cookies(self):
        """Deletes all the cookies the user sent with this request."""
        for name in self.cookies.iterkeys():
            self.clear_cookie(name)

    def get_cookie(self, name, default=None):
        """Gets the value of the cookie with the given name, else default."""
        if name in self.cookies:
            return self.cookies[name].value
        return default


    def get_secure_cookie(self, name, include_name=True, value=None):
        """Returns the given signed cookie if it validates, or None.

        In older versions of Tornado (0.1 and 0.2), we did not include the
        name of the cookie in the cookie signature. To read these old-style
        cookies, pass include_name=False to this method. Otherwise, all
        attempts to read old-style cookies will fail (and you may log all
        your users out whose cookies were written with a previous Tornado
        version).
        """
        if value is None:
            value = self.get_cookie(name)
        if not value: return None
        parts = value.split("|")

        if len(parts) != 3: return None
        if include_name:
            signature = self._cookie_signature(name, parts[0], parts[1])
        else:
            signature = self._cookie_signature(parts[0], parts[1])
        if not _time_independent_equals(parts[2], signature):
            logging.warning("Invalid cookie signature %r", value)
            return None
        timestamp = int(parts[1])
        if timestamp < time.time() - 31 * 86400:
            logging.warning("Expired cookie %r", value)
            return None
        if timestamp > time.time() + 31 * 86400:
            # _cookie_signature does not hash a delimiter between the
            # parts of the cookie, so an attacker could transfer trailing
            # digits from the payload to the timestamp without altering the
            # signature.  For backwards compatibility, sanity-check timestamp
            # here instead of modifying _cookie_signature.
            logging.warning("Cookie timestamp in future; possible tampering %r", value)
            return None
        if parts[1].startswith("0"):
            logging.warning("Tampered cookie %r", value)
        try:
            return base64.b64decode(parts[0])
        except:
            return None

    def _cookie_signature(self, *parts):
        hash = hmac.new(settings.COOKIE_SECRET, digestmod=hashlib.sha1)
        for part in parts: hash.update(part)
        return hash.hexdigest()

def _time_independent_equals(a, b):
    if len(a) != len(b):
        return False
    result = 0
    for x, y in zip(a, b):
        result |= ord(x) ^ ord(y)
    return result == 0
