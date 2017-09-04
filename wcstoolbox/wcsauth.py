"""calc auth"""
import json
import base64
import hmac
import time
from hashlib import sha1
from six.moves import urllib
import six

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
        encode_put_policy = base64.urlsafe_b64encode(six.b(json_put_policy))
        tmp_encode_put_policy = encode_put_policy
        sign = hmac.new(self.secret_key.encode('utf-8'),
                        encode_put_policy.encode('utf-8'), sha1)
        # encodeSign = base64.b64encode(Sign.hexdigest())
        encode_sign = base64.urlsafe_b64encode(sign.hexdigest())
        return '{0}:{1}:{2}'.format(self.access_key,
                                    encode_sign, tmp_encode_put_policy)

    def default_uploadtoken(self, bucket, key):
        """create default upload"""
        put_policy = {'scope': bucket + ':' + key,
                      'deadline': str(int(time.time()) * 1000 + 86400000),
                      'overwrite': 1, 'returnBody':
                      "url=$(url)&fsize=$(fsize)&bucket=$(bucket)\
                      &key=$(key)&hash=$(hash)\
                      &fsize=$(fsize)&mimeType=$(mimeType)\
                      &avinfo=$(avinfo)"}
        return self.uploadtoken(put_policy)

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
