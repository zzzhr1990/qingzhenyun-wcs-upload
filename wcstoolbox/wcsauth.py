import json
import base64
import hmac
from hashlib import sha1
from six.moves import urllib

"""
default config
"""

WCS_ACCESS_KEY = ''
WCS_SECRET_KEY = ''


class WcsAuth(object):

    """wcs auth
    upload token & manager token
    """

    @staticmethod
    def default_auth():
        """get default auth"""
        return WcsAuth(WCS_ACCESS_KEY, WCS_SECRET_KEY)

    def __init__(self, access_key, secret_key):
        self.check_key(access_key, secret_key)
        self.access_key = access_key
        self.secret_key = secret_key

    def uploadtoken(self, put_policy):
        """
        return: uploadtoken
        """

        # current = int(round(time.time() * 1000))

        # if putPolicy['deadline'] == None or putPolicy['deadline'] < current:
        #    raise ValueError("Invalid deadline")

        json_put_policy = json.dumps(put_policy)
        # encodePutPolicy = base64.b64encode(jsonputPolicy)
        encodePutPolicy = base64.urlsafe_b64encode(json_put_policy)
        tmp_encodePutPolicy = encodePutPolicy
        Sign = hmac.new(self.secret_key.encode('utf-8'),
                        encodePutPolicy.encode('utf-8'), sha1)
        # encodeSign = base64.b64encode(Sign.hexdigest())
        encodeSign = base64.urlsafe_b64encode(Sign.hexdigest())
        return '{0}:{1}:{2}'.format(self.access_key,
                                    encodeSign, tmp_encodePutPolicy)

    def managertoken(self, url, body=None):
        """
        return: managertoken
        """
        parsed_url = urllib.parse.urlparse(url)
        query = parsed_url.query
        path = parsed_url.path
        if query:
            if body:
                signing_str = ''.join([path, '?', query, "\n", body])
            else:
                signing_str = ''.join([path, '?', query, "\n"])
        else:
            if body:
                signing_str = ''.join([path, "\n", body])
            else:
                signing_str = ''.join([path, "\n"])
        sign_str = hmac.new(self.secret_key.encode('utf-8'),
                            signing_str.encode('utf-8'), sha1)
        encode_sign_str = base64.urlsafe_b64encode(sign_str.hexdigest())
        return '{0}:{1}'.format(self.access_key, encode_sign_str)

    @staticmethod
    def check_key(access_key, secret_key):
        """???"""
        if not (access_key and secret_key):
            raise ValueError('invalid key')
