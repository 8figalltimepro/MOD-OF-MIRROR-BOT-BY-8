import os
import mimetypes
import requests
from requests_toolbelt import MultipartEncoder
from requests_toolbelt.multipart.encoder import MultipartEncoderMonitor
from bot import GOFILE, GOFILEBASEFOLDER, GOFILETOKEN, LOGGER, DOWNLOAD_DIR, SERVERNUMBER
from logging import getLogger, WARNING
from time import time, sleep
from threading import RLock

LOGGER = getLogger(__name__)
getLogger("MultiPartEncoder").setLevel(WARNING)
servernumber = SERVERNUMBER

token = GOFILETOKEN

class GoFileUploader:
    def __init__(self, name=None, listener=None, createdfolderid=None):
        self.__listener = listener
        self.uploaded_bytes = 0
        self.__start_time = time()
        self.__is_cancelled = False
        self.createdfolderid = createdfolderid
        self.name = name
        self.folderpathd = []
        self.__resource_lock = RLock()

    def callback(self, monitor, chunk=(1024 * 1024 * 30), bytesread=0, bytestemp=0):
        bytesread += monitor.bytes_read
        bytestemp += monitor.bytes_read
        if bytestemp > chunk:
            self.uploaded_bytes = bytesread
            bytestemp = 0
        return

    def uploadThis(self):
        path = f"{DOWNLOAD_DIR}{self.__listener.uid}"
        if os.path.isfile(path + r'/{}'.format(self.name)):
            self.gofileupload_(filepath=(path + r'/{}'.format(self.name)), parentfolderid=self.createdfolderid)
        else:    
            self.uploadNow(path + r'/{}'.format(self.name), self.createdfolderid)
        self.folderpathd = []
        return

    def uploadNow(self, path, createdfolderid):  
        files = os.listdir(path)
        self.folderpathd.append(createdfolderid)
        for f in files:
            if os.path.isfile(path + r'/{}'.format(f)):
                self.gofileupload_(filepath=(path + r'/{}'.format(f)), parentfolderid=self.folderpathd[-1])
            elif os.path.isdir(path + r'/{}'.format(f)):
                subfolder = self.gofoldercreate_(foldername=f, parentfolderid=self.folderpathd[-1])
                y = subfolder['id']
                self.uploadNow(path + r'/{}'.format(f), y)
        del self.folderpathd[-1]
        return

    def gofileupload_(self, filepath, parentfolderid):
        filename = os.path.basename(filepath)
        mimetype = mimetypes.guess_type(filename)
        m = MultipartEncoder(
            fields={'file': (filename, open(filepath, 'rb'), mimetype), 'token': token, 'folderId': parentfolderid})
        monitor = MultipartEncoderMonitor(m, self.callback)
        headers = {'Content-Type': monitor.content_type}
        requests.post(f'https://store{servernumber}.gofile.io/uploadFile', data=monitor,
                      headers=headers)
        return 

    def gofoldercreate_(self, foldername, parentfolderid):
        m = {'folderName': foldername, 'token': token, 'parentFolderId': parentfolderid}
        x = requests.put('https://api.gofile.io/createFolder', data=m).json()['data']
        LOGGER.info(f'Created Folder {foldername}')
        return x

    @property
    def speed(self):
        with self.__resource_lock:
            try:
                return self.uploaded_bytes / (time() - self.__start_time)
            except ZeroDivisionError:
                return 0

    def cancel_download(self):
        self.__is_cancelled = True
        LOGGER.info(f"Cancelling Upload: {self.name}")
        self.__listener.onUploadError('your upload has been stopped!')
