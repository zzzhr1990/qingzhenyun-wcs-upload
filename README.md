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