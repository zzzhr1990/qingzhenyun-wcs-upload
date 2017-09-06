"""Used for wcs upload"""
import os
import requests
import logging
import math
from wcstoolbox.wcsutil import WcsUtil
import binascii
import time
import base64
import json
import six


class WcsSliceUploader(object):
    """New Upload For WCS"""

    def __init__(self, uploadtoken, filepath, put_url, params=None):
        self.uploadtoken = uploadtoken
        self.filepath = filepath
        self.put_url = put_url
        self.block_size = 1024 * 1024 * 4
        self.put_size = 512 * 1024
        self.make_file_retry = 5
        self.put_retry = 5
        self.make_block_retry = 5
        self.params = params
        self.size = os.path.getsize(self.filepath)
        self._calc_files()

    def _calc_files(self):
        self.num = int(math.ceil(1.0 * self.size / self.block_size))
        self.status = []
        self.offsetlist = [i * self.block_size for i in range(0, self.num)]

    def config_block_size(self, block_size):
        """Config block size"""
        if block_size > 0:
            self.block_size = block_size
            self._calc_files()

    def config_put_size(self, put_size):
        """Config put size"""
        if put_size > 0:
            self.put_size = put_size
            self._calc_files()

    def config_retry(self, put_retry, make_block_retry, make_file_retry):
        """Config Retry"""
        self.put_retry = put_retry
        self.make_block_retry = make_block_retry
        self.make_file_retry = make_file_retry

    def start_upload(self):
        """Start Upload"""
        upload_batch = WcsUtil.get_random_string()
        logging.info("%s has %d blocks.File size %ld, block size %d",
                     upload_batch, self.num, self.size, self.block_size)
        upload_ctxs = []
        block_id = 1
        for offset in self.offsetlist:
            succ = self._make_block(offset, upload_batch, block_id)
            if not succ:
                return -1, {"message": u'UploadFail'}
            upload_ctxs.append(succ)
            block_id = block_id + 1

        if len(upload_ctxs) != len(self.offsetlist):
            logging.warning("Uploaded blocks mismatch response.")
        code, body = self._make_file(upload_ctxs, upload_batch)
        if code != 200:
            logging.warning("Upload file to ws fail!")
        return code, body

    def _make_block(self, offset, upload_batch, block_id):
        with open(self.filepath, "rb") as openfile:
            bput = WcsUtil.readfile(openfile, offset, self.put_size)
            url = self._mlkblock_url(offset)
            headers = self._add_headers(upload_batch)
            blkretry = self.make_block_retry
            blockid = offset // self.block_size
            crc = binascii.crc32(bput) % (1 << 32)
            blkcode, blktext = self._do_post(
                url=url, headers=headers, data=bput)
            while self._need_repost(blkcode, blkretry, crc, blktext):
                blkcode, blktext = self._do_post(
                    url=url, headers=headers, data=bput)
                blkretry = blkretry - 1
            logging.debug("Block code %d, message %s", blkcode, blktext)
            if self._need_repost(blkcode, blkretry, crc, blktext) or \
                    blkcode != 200:
                logging.warning(
                    "make block file fail, code %d, response %s",
                    blkcode, json.dumps(blktext))
                return self._post_fail(u'MAKE_BLOCK_REQ_FAIL')
            if not blockid < self.num - 1:
                rest_block_size = self.size - \
                    (blockid * self.block_size) - self.put_size
                if not rest_block_size > 0:
                    return self._post_success(blktext['ctx'])
            offset, code, ctx = self._make_bput(
                openfile, blktext['ctx'], upload_batch, offset, block_id)
            if self._need_retry(code) or code != 200:
                logging.warning("make put file fail, code %d", code)
                return self._post_fail(u'MAKE_PUT_FAIL')
            else:
                return self._post_success(ctx)

    def _make_bput(self, inputfile, ctx, upload_batch, offset, block_id):
        bputnum = 1
        offset_next = offset + self.put_size
        bput_next = WcsUtil.readfile(inputfile, offset_next, self.put_size)
        bputretry = self.put_retry
        if bput_next is None:
            logging.warning("NONE_NOFILE")
            return offset, 200, ctx
        while bput_next is not None and \
                bputnum < self.block_size // self.put_size:
            start_time = time.time()
            bputcode, bputtext = self._make_bput_post(
                ctx, bputnum, upload_batch, bput_next)
            crc = binascii.crc32(bput_next) % (1 << 32)
            while self._need_repost(bputcode, bputretry, crc, bputtext):
                bputcode, bputtext = self._make_bput_post(
                    ctx, bputnum, upload_batch, bput_next)
                bputretry = bputretry - 1
            if self._need_repost(bputcode, 9999, crc, bputtext):
                logging.warning(
                    "upload put file fail, code %d, response %s",
                    bputcode, json.dumps(bputtext))
                return offset, bputcode, bputtext['message']
            time_cost = time.time() - start_time
            file_size = len(bput_next)
            speed = file_size / time_cost
            logging.debug(
                "Upload block %d of %d (pic:%d), file size %s, speed %s/sec",
                block_id, self.num, bputnum,
                WcsUtil.sizeof_fmt(file_size),
                WcsUtil.sizeof_fmt(speed))
            ctx = bputtext['ctx']
            offset_next = offset + bputtext['offset']
            bput_next = WcsUtil.readfile(inputfile, offset_next, self.put_size)
            bputnum += 1
        return offset, bputcode, ctx

    def _need_repost(self, status, retry, crc, body):
        if retry:
            if status != 200:
                return True
            if self._need_retry(status):
                return True
            if not body:
                return True
            if 'crc32' not in body:
                logging.warning("CRC Missing")
                return True
            if body['crc32'] != crc:
                logging.warning("CRC Mismatch")
                return True
        return False

    def _make_bput_post(self, ctx, bputnum, upload_batch, bput_next):
        url = self._bput_url(ctx, bputnum * self.put_size)
        headers = self._add_headers(upload_batch)
        return self._do_post(url=url, headers=headers, data=bput_next)

    def _file_headers(self, upload_batch):
        headers = {'Authorization': self.uploadtoken}
        headers['Content-Type'] = "text/plain"
        headers['uploadBatch'] = upload_batch
        return headers

    def _make_file(self, blockstatus, upload_batch):
        url = self._file_url(self.put_url)
        body = ','.join(blockstatus)
        # log.info('The ctx is %s, then start to make_file', body)
        headers = self._file_headers(upload_batch)
        retry = self.make_file_retry
        code, text = self._do_post(url=url, headers=headers, data=body)
        while retry and self._need_retry(code):
            # log.warning
            # ('Make_file fail, now start %dth retry',
            #  mkfile_retries - retry)
            code, text = self._do_post(url=url, headers=headers, data=body)
            retry -= 1
        if self._need_retry(code):
            logging.error('Sorry, the make_file error, code is %d', code)
            return -1, text
#           self.blockStatus = []
#            self.upload_progress_recorder.delete_upload_record(self.key)
#        else:
#           log.info('Make_file suc! wcssliceupload complet!')
        return code, text

    def _file_url(self, host):
        url = ['{0}/mkfile/{1}'.format(host, self.size)]
        if self.params:
            for k, v in self.params.items():
                url.append('x:{0}/{1}'.format(k, six.
                                              b(base64.urlsafe_b64encode(v))))
        url = '/'.join(url)
        return url

    def _bput_url(self, ctx, offset):
        return '{0}/bput/{1}/{2}'.format(self.put_url, ctx, offset)

    def _post_fail(self, res=u'unknown'):
        logging.error("POST FILE FAIL!!!! %s", res)
        return None

    def _post_success(self, ctx):
        return ctx

    def _do_post(self, url, headers, data):
        return WcsUtil.do_wcs_post(url, headers, data)

    def _add_headers(self, upload_batch):
        headers = {'Authorization': self.uploadtoken}
        headers['Content-Type'] = "application/octet-stream"
        headers['uploadBatch'] = upload_batch
        return headers

    def _mlkblock_url(self, offset):
        blockid = offset // self.block_size
        if blockid < self.num - 1:
            url = self._block_url(self.block_size, blockid)
        else:
            url = self._block_url(
                self.size - (blockid * self.block_size), blockid)
        return url

    def _need_retry(self, code):
        return WcsUtil.wcs_need_retry(code)

    def _block_url(self, size, blocknum):
        return '{0}/mkblk/{1}/{2}'.format(self.put_url, size, blocknum)
