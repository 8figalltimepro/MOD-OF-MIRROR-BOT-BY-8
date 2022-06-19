import os
import mimetypes
import requests
from requests_toolbelt import MultipartEncoder
from bot import GOFILE, GOFILEBASEFOLDER, GOFILETOKEN, LOGGER

folderpathd = []
def uploadThis(path, createdfolderid):
    files = os.listdir(path)
    folderpathd.append(createdfolderid)
    for f in files:
        if os.path.isfile(path + r'/{}'.format(f)):
            gofileupload_(filepath=(path + r'/{}'.format(f)), parentfolderid=folderpathd[-1])
        elif os.path.isdir(path + r'/{}'.format(f)):
            subfolder = gofoldercreate_(foldername=f, parentfolderid=folderpathd[-1])
            y = subfolder['id']
            uploadThis(path + r'/{}'.format(f), y)
    del folderpathd[-1]
    return 
  
token = GOFILETOKEN


def gofileupload_(filepath, parentfolderid):
    filename = os.path.basename(filepath)
    mimetype = mimetypes.guess_type(filename)
    m = MultipartEncoder(fields={'file': (filename, open(filepath, 'rb'), mimetype), 'token': token, 'folderId': parentfolderid})
    x = requests.post('https://store1.gofile.io/uploadFile', data=m,
                      headers={'Content-Type': m.content_type})
    return

def gofoldercreate_(foldername, parentfolderid):
    m = {'folderName': foldername, 'token': token, 'parentFolderId': parentfolderid}
    x = requests.put('https://api.gofile.io/createFolder', data=m).json()['data']
    LOGGER.info(f'Created Folder {foldername}')
    return x
