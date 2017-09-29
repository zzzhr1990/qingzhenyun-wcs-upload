from wcstoolbox.mgrbase import MgrBase
import logging
import time
from wcstoolbox.wcsutil import WcsUtil


class WcsBucketManager(MgrBase):
    """manage"""

    #    def __init__(self, auth, mgr_url):
    #    super(BucketManager, self).__init__(auth, mgr_url)

    def _limit_check(self):
        n_max = 0
        while n_max < 1000:
            yield n_max
            n_max += 1

    def _make_delete_url(self, bucket, key):
        return '{0}/delete/{1}'.format(self.mgr_host, WcsUtil
                                       .wcs_entry(bucket, key))

    def _do_retry_post(self, url, headers, data=None):
        try_time = 3
        while(try_time > 0):
            code, result = WcsUtil.do_wcs_post(url, headers, data)
            if code < 400:
                return code, result
            try_time = try_time - 1
            time.sleep(1)
        return -1, {"message": "Retry Timeout"}

    def _do_retry_get(self, url, headers, data=None):
        try_time = 3
        while(try_time > 0):
            code, result = WcsUtil.do_wcs_get(url, headers, data)
            if code < 400:
                return code, result
            try_time = try_time - 1
            time.sleep(1)
        return -1, {"message": "Retry Timeout"}

    def delete(self, bucket, key):
        """delete file"""
        url = self._make_delete_url(bucket, key)
        logging.debug('Start to post request of delete %s:%s', bucket, key)
        code, text = self._do_retry_post(url=url, headers=self.
                                         _gernerate_headers(url))
        logging.debug('Return code is %d and text of delete request is: %s',
                      code, text)
        return code, text

    def _make_filestat_url(self, bucket, key):
        return '{0}/stat/{1}'.format(self.mgr_host,
                                     WcsUtil.wcs_entry(bucket, key))

    def stat(self, bucket, key):
        """get file stat"""
        url = self._make_filestat_url(bucket, key)
        logging.debug('Start to get the stat of %s:%s', bucket, key)
        code, text = self._do_retry_get(url=url,
                                        headers=self._gernerate_headers(url))
        logging.debug('The return code : %d and text : %s', code, text)
        return code, text

    def _make_list_url(self, param):
        url = ['{0}/list'.format(self.mgr_host)]
        if param:
            url.append(self._params_parse(param))
        url = '?'.join(url)
        return url

    def bucketlist(self, bucket, prefix=None, marker=None, limit=None,
                   mode=None):
        """list"""
        options = {
            'bucket': bucket,
        }
        if marker:
            options['marker'] = marker
        if limit:
            if limit in self._limit_check():
                options['limit'] = limit
            else:
                logging.error('Invalid limit ! Please redefine limit')
                raise ValueError("Invalid limit")
        if prefix:
            options['prefix'] = prefix
        if mode:
            options['mode'] = mode
        url = self._make_list_url(options)
        if options:
            logging.debug('List options is %s', options)
        logging.debug('List bucket %s', bucket)
        code, text = WcsUtil.\
            do_wcs_get(url=url, data=options,
                       headers=self._gernerate_headers(url))
        logging.debug('The return code : %d and text : %s', code, text)
        return code, text

    def _make_move_url(self, srcbucket, srckey, dstbucket, dstkey):
        src = WcsUtil.urlsafe_base64_encode('%s:%s' % (srcbucket, srckey))
        dst = WcsUtil.urlsafe_base64_encode('%s:%s' % (dstbucket, dstkey))
        url = '{0}/move/{1}/{2}'.format(self.mgr_host, src, dst)
        return url

    def move(self, srcbucket, srckey, dstbucket, dstkey):
        url = self._make_move_url(srcbucket, srckey, dstbucket, dstkey)
        logging.debug('Move object %s from %s to %s:%s',
                      srckey, srcbucket, dstbucket, dstkey)
        code, text = WcsUtil.\
            do_wcs_post(url=url, headers=self._gernerate_headers(url))
        logging.debug('The return code : %d and text : %s', code, text)
        return code, text

    def _make_copy_url(self, srcbucket, srckey, dstbucket, dstkey):
        src = WcsUtil.urlsafe_base64_encode('%s:%s' % (srcbucket, srckey))
        dst = WcsUtil.urlsafe_base64_encode('%s:%s' % (dstbucket, dstkey))
        url = '{0}/copy/{1}/{2}'.format(self.mgr_host, src, dst)
        return url

    def copy(self, srcbucket, srckey, dstbucket, dstkey):
        url = self._make_copy_url(srcbucket, srckey, dstbucket, dstkey)
        logging.debug('Copy object %s from %s to %s:%s',
                      srckey, srcbucket, dstbucket, dstkey)
        code, text = self._do_retry_post(url=url,
                                         headers=self._gernerate_headers(url))
        logging.debug('The return code : %d and text : %s', code, text)
        return code, text

    def setdeadline(self, bucket, key, deadline):
        url = '{0}/setdeadline'.format(self.mgr_host)
        param = {
            'bucket': WcsUtil.urlsafe_base64_encode(bucket),
        }
        param['key'] = WcsUtil.urlsafe_base64_encode(key)
        param['deadline'] = deadline
        body = self._params_parse(param)
        logging.debug('Set deadline of %s to %s', key, deadline)
        code, text = self._do_retry_post(url=url, data=body,
                                         headers=self._gernerate_headers(url,
                                                                         body))
        logging.debug('The return code : %d and text : %s', code, text)
        return code, text

    def uncompress(self, fops, bucket, key, notifyurl=None,
                   force=None, separate=None):
        url = '%s/fops' % self.mgr_host
        options = {'bucket': WcsUtil.urlsafe_base64_encode(bucket),
                   'key': WcsUtil.urlsafe_base64_encode(key),
                   'fops': WcsUtil.urlsafe_base64_encode(fops)
                   }
        if notifyurl:
            options['notifyurl'] = WcsUtil.urlsafe_base64_encode(notifyurl)
        if force:
            options['force'] = force
        if separate:
            options['separate'] = separate
        body = self._params_parse(options)
        logging.debug('Uncompress of %s : %s', bucket, key)
        code, text = self._do_retry_post(url=url, data=body, headers=self.
                                         _gernerate_headers(url, body))
        logging.debug('The return code : %d and text : %s', code, text)
        return code, text
