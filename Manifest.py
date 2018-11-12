import sqlite3
import requests
import zipfile
import os
import json
from app import app


class Database:

    def __init__(self, datafile):
        self.__conn = sqlite3.connect(datafile)

    def selectQuery(self, id, table):
        c = self.__conn.cursor()
        query = str.format('SELECT json FROM {} where id={}', table, str(id))
        c.execute(query)
        data = c.fetchall()
        if data:
            result = json.loads(data[0][0])
            return result
        else:
            return {}


def getDatabaseConnection():
    return Database(app.config['MANIFEST_FILE'])


def HashtoID(hash):
    hash = int(hash)
    if (hash & (1 << (32 - 1))) != 0:
        hash = hash - (1 << 32)
    return hash


def getManifestVersion():
    MANIFEST_URL = 'https://www.bungie.net/Platform/Destiny2/Manifest/'
    KEY = '7301e8cb17564c64b12cfa5a0518e54f'
    HEADERS = {'X-API-Key': KEY}
    return requests.get(MANIFEST_URL, headers=HEADERS)


def downloadManifest(content, path):
    BASE_URL = 'https://www.bungie.net/'
    response = requests.get(BASE_URL + content, stream=True)
    handle = open(path, "wb")
    for chunk in response.iter_content(chunk_size=512):
        if chunk:  # filter out keep-alive new chunks
            handle.write(chunk)


def extractManifest(file, destination):
    with zipfile.ZipFile(file) as zf:
        zf.extractall(destination)

#TODO: Make this dynamic to FS pathing (broke on linux)
#TODO: Have this update config? or write a static file?
def updateManifest():
    r = getManifestVersion()
    my_json = json.loads(r.content.decode('utf-8'))
    mWCP = my_json['Response']['mobileWorldContentPaths']['en']
    filepath = os.path.dirname(os.path.realpath('__file__'))
    mWCPpath = os.path.join(filepath, 'db\zip\mWCP.content')
    downloadManifest(mWCP, mWCPpath)
    extractManifest(mWCPpath, 'db\\')


if __name__ == "__main__":
    updateManifest()
