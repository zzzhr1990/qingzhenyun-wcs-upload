import string
import random
import hashlib
import binascii
import six
import logging
import base64
import requests
import magic
import json
import traceback
import sys
from io import BytesIO
from requests.exceptions import Timeout
from requests.exceptions import ConnectionError as RConnectionError
from wcstoolbox.wcsauth import WcsAuth
from base64 import urlsafe_b64encode, urlsafe_b64decode
import pycurl


class WcsUtil(object):
    @staticmethod
    def get_random_string(length=32):
        """Get ramdom str"""
        chars = string.ascii_letters + string.digits
        return ''.join([random.choice(chars) for i in range(length)])

    @staticmethod
    def readfile(input_stream, offset, size):
        """Read file fro, offset"""
        input_stream.seek(offset)
        dest = input_stream.read(size)
        if dest:
            return dest

    @staticmethod
    def md5(str_s):
        """calc md5"""
        m_uu = hashlib.md5()
        m_uu.update(str_s)
        return m_uu.hexdigest()

    @staticmethod
    def sha1(data):
        """Calc SHA1"""
        sha_hash = hashlib.sha1()
        sha_hash.update(data)
        return sha_hash.digest()

    @staticmethod
    def urlsafe_base64_encode(data):
        """urlsafe的base64编码:
        对提供的数据进行urlsafe的base64编码。规格参考：
        Args:
            data: 待编码的数据，一般为字符串
        Returns:
            编码后的字符串
        """
        ret = urlsafe_b64encode(six.b(data))
        return ret.decode('utf-8')

    @staticmethod
    def urlsafe_base64_decode(data):
        """urlsafe的base64解码:
        对提供的urlsafe的base64编码的数据进行解码
        Args:
            data: 待解码的数据，一般为字符串
        Returns:
            解码后的字符串。
        """
        ret = urlsafe_b64decode(data.encode('utf-8'))
        return ret

    @staticmethod
    def wcs_etag(file_path, block_size=1024 * 1024 * 4, binary=False):
        """Calc WCS Etag(FileHash)"""
        with open(file_path, 'rb') as input_stream:
            array = [WcsUtil.sha1(block) for block in WcsUtil.file_iter(
                input_stream, 0, block_size)]
            block_len = len(array)
            if block_len == 0:
                array = [WcsUtil.sha1(b'')]
            if block_len == 1:
                data = array[0]
                prefix = b'\x16'
            else:
                sha1_str = six.b('').join(array)
                data = WcsUtil.sha1(sha1_str)
                prefix = b'\x96'
            if binary:
                return base64.urlsafe_b64encode(prefix + data)
            return base64.urlsafe_b64encode(prefix + data).decode('utf-8')

    @staticmethod
    def wcs_etag_bytes(buff, block_size=1024 * 1024 * 4):
        """Calc WCS Etag(FileHash)"""
        with BytesIO(buff) as input_stream:
            array = [WcsUtil.sha1(block) for block in WcsUtil.file_iter(
                input_stream, 0, block_size)]
            if not array:
                array = [WcsUtil.sha1(b'')]
            if len(array) == 1:
                data = array[0]
                prefix = b'\x16'
            else:
                sha1_str = six.b('').join(array)
                data = WcsUtil.sha1(sha1_str)
                prefix = b'\x96'
            return base64.urlsafe_b64encode(prefix + data)

    @staticmethod
    def file_iter(input_stream, offset, size):
        """Read input stream"""
        input_stream.seek(offset)
        d_read = input_stream.read(size)
        while d_read:
            yield d_read
            d_read = input_stream.read(size)

    @staticmethod
    def mime(file_path):
        """Get mime"""
        file_mime = u"application/octet-stream"
        try:
            file_mime = magic.from_file(file_path, mime=True)
        except Exception:
            file_mime = u"application/octet-stream"
        return file_mime

    @staticmethod
    def mime_buffer(file_path):
        """Get mime"""
        file_mime = u"application/octet-stream"
        try:
            file_mime = magic.from_buffer(file_path, mime=True)
        except Exception:
            file_mime = u"application/octet-stream"
        return file_mime

    @staticmethod
    def to_ascii(ustr):
        """UTF8 Strings to ascii(py2)"""
        return ustr.encode('utf8')

    @staticmethod
    def crc32(data):
        """Calc crc32"""
        return binascii.crc32(six.b(data)) & 0xffffffff

    @staticmethod
    def do_wcs_post(url, headers, data=None):
        """Post to wcs"""
        buffer = BytesIO()
        curl = pycurl.Curl()
        curl.setopt(pycurl.POST, 1)
        curl.setopt(pycurl.CONNECTTIMEOUT, 5)
        curl.setopt(pycurl.TIMEOUT, 10)
        if headers:
            post_header = []
            for key, value in headers.items():
                post_header.append("%s: %s" % (key, value))
            curl.setopt(pycurl.HTTPHEADER, post_header)
        if data:
            curl.setopt(pycurl.POSTFIELDS, data)
        curl.setopt(pycurl.URL, url)
        curl.setopt(pycurl.FOLLOWLOCATION, True)
        curl.setopt(pycurl.WRITEDATA, buffer)
        curl.setopt(pycurl.NOSIGNAL, 1)
        status_code = 0
        try:
            curl.perform()
            status_code = curl.getinfo(pycurl.RESPONSE_CODE)
        except Exception:
            exc_type, exc_value, exc_traceback = sys.exc_info()
            lines = traceback.format_exception(
                exc_type, exc_value, exc_traceback)
            logging.error(''.join('!--! ' + line for line in lines))
        finally:
            curl.close()
        if status_code < 400 and status_code > 0:
            return status_code, json.loads(buffer.getvalue().decode('utf-8'))
        return status_code, {"message": "request error"}
        """
        try:
            resp = requests.post(
                url, data=data, headers=headers, timeout=(5, 5))
            if WcsUtil.wcs_need_retry(resp.status_code):
                return -1, {}
            else:
                try:
                    return resp.status_code, resp.json()
                except Exception:
                    logging.warning("%s exception", url)
                    return resp.status_code, {"message": resp.text}
        except Timeout:
            logging.warning("%s timeout", url)
            return -1, {"message": "connection Timeout"}
        except RConnectionError:
            logging.warning("%s connection error", url)
            return -1, {"message": "connection Error"}
        """

    @staticmethod
    def _debug_fun(debug_type, debug_msg):
        logging.debug("%s - %s", debug_type, debug_msg)

    @staticmethod
    def do_wcs_get(url, headers=None, data=None):
        """Post to wcs"""

        buffer = BytesIO()
        curl = pycurl.Curl()
        if headers:
            post_header = []
            for key, value in headers.items():
                post_header.append("%s: %s" % (key, value))
            curl.setopt(pycurl.HTTPHEADER, post_header)
        curl.setopt(pycurl.URL, url)
        curl.setopt(pycurl.CONNECTTIMEOUT, 5)
        curl.setopt(pycurl.TIMEOUT, 10)
        curl.setopt(pycurl.FOLLOWLOCATION, True)
        curl.setopt(pycurl.WRITEDATA, buffer)
        curl.setopt(pycurl.NOSIGNAL, 1)
        # curl.setopt(pycurl.VERBOSE, 1)
        # curl.setopt(pycurl.DEBUGFUNCTION, WcsUtil._debug_fun)
        # debug enable
        status_code = 0
        try:
            logging.debug("Starting get %s", url)
            curl.perform()
            status_code = curl.getinfo(pycurl.RESPONSE_CODE)
            logging.debug("Finish get %s - %d", url, status_code)
        except Exception:
            logging.debug("Error get %s", url)
            exc_type, exc_value, exc_traceback = sys.exc_info()
            lines = traceback.format_exception(
                exc_type, exc_value, exc_traceback)
            logging.error(''.join('!--! ' + line for line in lines))
        finally:
            curl.close()
        if status_code < 400 and status_code > 0:
            return status_code, json.loads(buffer.getvalue().decode('utf-8'))
        return status_code, {"message": "request error"}

        """
        try:
            resp = requests.get(
                url, data=data, headers=headers, timeout=(5, 5))
            if WcsUtil.wcs_need_retry(resp.status_code):
                return -1, {}
            else:
                try:
                    return resp.status_code, resp.json()
                except Exception:
                    logging.warning("%s exception", url)
                    return resp.status_code, {"message": resp.text}
        except Timeout:
            logging.warning("%s timeout", url)
            return -1, {"message": "connection Timeout"}
        except RConnectionError:
            logging.warning("%s connection error", url)
            return -1, {"message": "connection Error"}
        """

    @staticmethod
    def wcs_need_retry(code):
        """N"""
        if code == -1:
            return True
        if code // 100 == 5 and code != 579:
            return True
        return False

    @staticmethod
    def wcs_entry(bucket, key):
        """Calc e"""
        if key is None:
            return base64.urlsafe_b64encode(six.b('{0}'.format(bucket)))\
                .decode('utf-8')
        else:
            return base64.urlsafe_b64encode(six.b('{0}:{1}'
                                                  .format(bucket, key)))\
                .decode('utf-8')

    @staticmethod
    def default_wcs_auth():
        """c"""
        return WcsAuth.default_auth()

    @staticmethod
    def sizeof_fmt(num, suffix='B'):
        """nf"""
        for unit in ['', 'K', 'M', 'G', 'T', 'P', 'E', 'Z']:
            if abs(num) < 1024.0:
                return "%3.1f%s%s" % (num, unit, suffix)
            num /= 1024.0
        return "%.1f%s%s" % (num, 'Y', suffix)

    @staticmethod
    def get_wcs_avinfo(host, key):
        """Check This File Status"""
        try:
            req = requests.get(host + "/" + key + "?op=avinfo", timeout=60)
            if req.status_code != 200:
                return {}
            return req.json()
        except Exception:
            return {}
