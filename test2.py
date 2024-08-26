import base64
from Crypto.Cipher import AES
from Crypto.Util.Padding import unpad
import json

EAPI_KEY = b"e82ckenh8dichen8"
EAPI_CRYPTOR = AES.new(EAPI_KEY, AES.MODE_ECB)

def data_decrypt(enc_data):
    data = unpad(EAPI_CRYPTOR.decrypt(enc_data), 16).decode()
    return json.loads(data)

if __name__ == "__main__":
    data = None
    with open("a.txt","rb") as f:
        data = f.read()
    print(
        data_decrypt(data
        )
    )