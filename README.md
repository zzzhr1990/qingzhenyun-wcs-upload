# wcs toolbox for qingzhenyun

###

wcssliceuploader

WcsBucketManager

### Usage:

#### WcsSliceUploader

```python
from wcstoolbox.wcssliceuploader import WcsSliceUploader
from wcstoolbox.wcsauth import WcsAuth

# APP_KEY, SECRET_KEY, PUT_URL need to ask chinanetcenter to get it.
auth = WcsAuth(APP_KEY, SECRET_KEY)
putpolicy = {'scope': 'other-storage:' + file_key,
                     'deadline': str(int(time.time()) * 1000 + 86400000),
                     'overwrite': 1, 'returnBody':
                     'url=$(url)&fsize=$(fsize)&bucket=$(bucket)&key=$(key)&hash=$(hash)&fsize=$(fsize)&mimeType=$(mimeType)&avinfo=$(avinfo)'}
token = auth.uploadtoken(putpolicy)
upload = WcsSliceUploader(token, FILE_PATH, PUT_URL)
start_time = time.time()
code, body = upload.start_upload()
time_cost = time.time() - start_time
speed = file_size / time_cost
logging.info("file %s:%s filesize uploaded %s/sec", file_path,
                     Util.sizeof_fmt(file_size), Util.sizeof_fmt(speed))
if code != 200:
    #fail
    pass
etag = body["hash"]
# process return json
```
```
Python 3.6.2 (default, Jul 17 2017, 16:44:45)
[GCC 4.2.1 Compatible Apple LLVM 8.1.0 (clang-802.0.42)] on darwin
Type "help", "copyright", "credits" or "license" for more information.
>>> from wcstoolbox.wcssliceuploader import WcsSliceUploader
>>> from wcstoolbox.wcsauth import WcsAuth
>>> import logging
>>> logging.basicConfig(level=logging.DEBUG,format='%(asctime)s %(filename)s[line:%(lineno)d] %(levelname)s %(message)s',datefmt='%Y-%m-%d %H:%M:%S')
>>> upload_url = URL
>>> auth = WcsAuth(AK,SK)
>>> upload_token = auth.default_uploadtoken('other-storage','test/test.5678.9.0.1')
>>> upload_token = auth.default_uploadtoken('other-storage','test/test.5678.9.0.2')
>>> uploader = WcsSliceUploader(upload_token, '/Users/zzzhr/Downloads/ubuntu-17.04-server-amd64.iso', upload_url)
>>> uploader.start_upload()
```