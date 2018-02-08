from wcstoolbox.mgrbase import MgrBase
import logging
import time
from wcstoolbox.wcsutil import WcsUtil


class WcsPersistentFop(MgrBase):
    """do fops"""

    def _build_op(self, cmd, first_arg, **kwargs):
        op = [cmd]
        if first_arg is not None:
            op.append(first_arg)

        for k, v in kwargs.items():
            op.append('{0}/{1}'.format(k, v))
        return '/'.join(op)

    def _pipe_cmd(self, *cmds):
        return '|'.join(cmds)

    def _op_save(self, op, bucket, key):
        return self._pipe_cmd(op, 'saveas/' + WcsUtil.entry(bucket, key))

    def build_ops(self, ops, bucket, key):
        ops_list = []
        for op, params in ops.items():
            ops_list.append(self._op_save(
                self._build_op(op, params), bucket, key))
        return ops_list

    def fops_status(self, persistentId):
        """https check?"""
        url = WcsUtil.https_check(
            '{0}/status/get/prefop?persistentId={1}'.format(self.mgr_host, persistentId))
        logging.debug('Start to get status of persistentId: %s', persistentId)
        return WcsUtil.do_wcs_get(url=url)

    def _gernerate_headers(self, url, data):
        reqdata = super(WcsPersistentFop, self)._params_parse(data)
        headers = super(WcsPersistentFop, self)._gernerate_headers(
            url, body=reqdata)
        return headers, reqdata

    def execute(self, fops, bucket, key, force=0, separate=0, notifyurl=None):
        data = {'bucket': WcsUtil.urlsafe_base64_encode(bucket),
                'key': WcsUtil.urlsafe_base64_encode(
            key), 'fops': WcsUtil.urlsafe_base64_encode(fops)}
        if notifyurl is not None:
            data['notifyURL'] = WcsUtil.urlsafe_base64_encode(notifyurl)
        if force == 1:
            data['force'] = 1
        if separate == 1:
            data['separate'] = 1
        url = WcsUtil.https_check('{0}/fops'.format(self.mgr_host))
        headers, reqdata = self._gernerate_headers(url, data)
        logging.debug('PersistentFops is %s', fops)
        logging.debug('Start to post persistentFops')
        return WcsUtil.do_wcs_post(url=url, data=reqdata, headers=headers)
