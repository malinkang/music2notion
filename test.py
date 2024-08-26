import base64
from Crypto.Cipher import AES
from Crypto.Util.Padding import unpad
import json

EAPI_KEY = b"e82ckenh8dichen8"
EAPI_CRYPTOR = AES.new(EAPI_KEY, AES.MODE_ECB)


def eapi_decrypt(enc_data):
    message = unpad(EAPI_CRYPTOR.decrypt(base64.b16decode(enc_data)), 16).decode()
    path, json_val, hash = message.split("-36cd479b6b5-")
    with open("r.json","w") as f:
       f.write(json.dumps(json.loads(json_val),indent=4,ensure_ascii=False))
    # return path, json.loads(json_val)


if __name__ == "__main__":
  with open("params","r") as f:
     data = f.read()
     print(data)
     print(eapi_decrypt(data))
