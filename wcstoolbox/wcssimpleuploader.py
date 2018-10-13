import logging
import math
import os
import time
import json
from wcstoolbox.wcsutil import WcsUtil
from concurrent.futures import ThreadPoolExecutor

class WcsSimpleUploader(object):
    """New Simple Uploader For WCS"""
    def __init__(self,
                 uploadtoken,
                 filepath,
                 put_url, file_id=WcsUtil.get_random_string(32),
                 params=None):
        self.uploadtoken = uploadtoken
        self.filepath = filepath
        self.put_url = put_url
        #self.block_size = block_size
        self.block_size = 1024 * 1024 * 4
        self.make_file_retry = 5
        self.put_retry = 5
        self.make_block_retry = 5
        self.params = params
        self.size = os.path.getsize(self.filepath)
        #self._calc_files()
        self.file_id = file_id
        self.terminate = False
        self.mime_type = ''
        self.progress_listener = []
        #self.last_time = time.time()

    def add_progress_listener(self, listener):
        """add listener"""
        self.progress_listener.append(listener)

    def start_multi_thread_upload(self, thread_num):
        blocks = self.size // self.block_size
        total_blocks = blocks
        block_info = {}
        if blocks > 0:
            for i in range(0,blocks):
                block_info[str(i)] = {'index':i, 'offset':i * self.block_size, 'size':self.block_size}
        last_piece = self.size % self.block_size
        if last_piece > 0:
            total_blocks = blocks + 1
            block_info[str(blocks)] = {'index':blocks, 'offset':blocks * self.block_size, 'size':last_piece}
        # 
        if total_blocks < thread_num:
            thread_num = total_blocks
        pool = ThreadPoolExecutor(max_workers=thread_num)
        for key in block_info:
            fn = pool.submit(self._read_and_post,(block_info[key],))
            block_info[key]['fn'] = fn
            logging.warning('DONE? %s',fn.done())
            logging.warning('DONE? %s',fn.done())
            logging.warning('DONE? %s',fn.done())
            #fn.add_done_callback(lambda)
        # check if done
        all_done = False
        while not all_done:
            flg = True
            for key in block_info:
                fn = block_info[key]['fn']
                if not fn.done():
                    logging.warning('FLG_FALSE')
                    flg = False
                else:
                    logging.warning('FLG_DONE')
            if not flg:
                time.sleep(1)
            all_done = flg
            if all_done:
                logging.warning('ALLLLLLLDONE')
            else:
                logging.warning('NOT_ALL_DONE')
        # all down
        logging.warning('DONE_____')
        blocks_ctx_str = ''
        for i in range(0,total_blocks):
            key = str(i)
            fn = block_info[key]['fn']
            block_ctx = fn.result()
            if not block_ctx:
                logging.warning('File post failed.')
                return -1, {"message": "Post Failed"}
            if i > 0:
                blocks_ctx_str = blocks_ctx_str + ',' + block_ctx
            else:
                blocks_ctx_str = blocks_ctx_str + block_ctx
        file_hash = self._make_file(blocks_ctx_str, self.size)
        if not file_hash:
            return -1, {"message": "Post Failed"}
        return 200, {"hash": file_hash}

    def _read_and_post(self,block_info):
        try:
            logging.warning('Start Post %d', block_info['index'])
            #time.sleep(200)
            with open(self.filepath, 'rb') as input_stream:
                logging.warning('READ_FILE')
                if block_info['offset'] > 0:
                    input_stream.seek(block_info['offset'])
                    logging.warning('SEEEK')
                d_read = input_stream.read(self.block_size)
                logging.warning('READ')
                block_ctx = self._post_block(d_read, block_info['index'], len(d_read))
                logging.warning('End Post')
                if not block_ctx:
                    return None
                return block_ctx
        except Exception as identifier:
            logging.exception('ex %s', identifier)
            return None
        
    def start_upload(self):
        """Start Upload"""
        # Read file...
        with open(self.filepath, 'rb') as input_stream:
            blocks = ''
            read_size = 0
            index = 0
            while True:
                d_read = input_stream.read(self.block_size)
                if not d_read:
                    break
                current_read_size = len(d_read)
                block_ctx = self._post_block(d_read, index, current_read_size)
                if not block_ctx:
                    logging.warning('File post failed.')
                    return -1, {"message": "Post Failed"}
                
                read_size = read_size + current_read_size
                if index > 0:
                    blocks = blocks + ',' + block_ctx
                else:
                    blocks = blocks + block_ctx
                # logging.warning('BLOCK %ld post', index)
                if self.progress_listener:
                    progress_obj = {'index':index, 'file_size':self.size, 'post_size':read_size}
                    for func in self.progress_listener:   
                        try:
                            func(progress_obj)
                        except Exception as ex:
                            logging.exception('call listener error %s', ex)
                index = index + 1
            file_hash = self._make_file(blocks, read_size)
            if not file_hash:
                return -1, {"message": "Post Failed"}
            return 200, {"hash": file_hash}
            # logging.warning('FIN %d - %d', read_size, self.size)

    def set_mime_type(self, mime_type):
        """set mime"""
        self.mime_type = mime_type

    def _make_file(self, blocks, read_size):
        post_url = '%s/mkfile/%ld' % (self.put_url,read_size,)
        try_time = 100
        while try_time > 0:
            headers = {'Authorization': self.uploadtoken}
            headers['Content-Type'] = "text/plain"
            headers['uploadBatch'] = self.file_id
            if self.mime_type:
                headers['MimeType'] = self.mime_type
                headers['Mime-Type'] = self.mime_type
            status_code, response_json = WcsUtil.do_wcs_post(post_url, headers,blocks)
            if status_code == 200:
                if 'hash' in response_json:
                    return response_json['hash']
            try_time = try_time - 1
            logging.warning('Make file failed, status code %d, reason %s', status_code, json.dumps(response_json))
            time.sleep(10)
        logging.warning('Give up make file id %s:%s', self.file_id,self.filepath)
        return ''

    def _post_block(self, read_buffer, block_index, current_read_size):
        post_url = '%s/mkblk/%ld/%ld' % (self.put_url,current_read_size, block_index,)
        #logging.warning('POST %s', post_url)
        try_time = 100
        while try_time > 0:
            # try
            headers = {'Authorization': self.uploadtoken}
            headers['Content-Type'] = "application/octet-stream"
            headers['uploadBatch'] = self.file_id
            status_code, response_json = WcsUtil.do_wcs_post(post_url, headers,read_buffer)
            if status_code == 200:
                if 'ctx' in response_json:
                    return response_json['ctx']
            try_time = try_time - 1
            logging.warning('Post block failed, status code %d, reason %s', status_code, json.dumps(response_json))
            time.sleep(10)
        logging.warning('Give up post file id %s:%s', self.file_id,self.filepath)
        return ''

