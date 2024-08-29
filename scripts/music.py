import os
import json
from requests.auth import HTTPBasicAuth
import pendulum
from retrying import retry
import requests
from notion_helper import NotionHelper
import utils
import time
import binascii
import hashlib
import requests
import json
from Crypto.Cipher import AES
from Crypto.Util.Padding import unpad
from cryptography.hazmat.backends import default_backend
from cryptography.hazmat.primitives import padding
from cryptography.hazmat.primitives.ciphers import Cipher, algorithms, modes

from config import song_properties_type_dict, USER_ICON_URL
from utils import get_icon, split_emoji_from_string
from dotenv import load_dotenv

# AES 解密函数
EAPI_KEY = b"e82ckenh8dichen8"
EAPI_CRYPTOR = AES.new(EAPI_KEY, AES.MODE_ECB)
load_dotenv()
headers = {
    "Accept": "*/*",
    "Content-Type": "application/x-www-form-urlencoded",
    "MG-Product-Name": "music",
    "Nm-GCore-Status": "1",
    "Origin": "orpheus://orpheus",
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; WOW64) AppleWebKit/537.36 (KHTML, like Gecko)"
    " Chrome/35.0.1916.157 NeteaseMusicDesktop/2.9.7.199711 Safari/537.36",
    "Accept-Encoding": "gzip,deflate",
    "Accept-Language": "en-us,en;q=0.8",
}

import random


def cnip():
    # 国内城市IP段
    ips = "58.14.0.0,58.16.0.0,58.24.0.0,58.30.0.0,58.32.0.0,58.66.0.0,58.68.128.0,58.82.0.0,58.87.64.0,58.99.128.0,58.100.0.0,58.116.0.0,58.128.0.0,58.144.0.0,58.154.0.0,58.192.0.0,58.240.0.0,59.32.0.0,59.64.0.0,59.80.0.0,59.107.0.0,59.108.0.0,59.151.0.0,59.155.0.0,59.172.0.0,59.191.0.0,59.191.240.0,59.192.0.0,60.0.0.0,60.55.0.0,60.63.0.0,60.160.0.0,60.194.0.0,60.200.0.0,60.208.0.0,60.232.0.0,60.235.0.0,60.245.128.0,60.247.0.0,60.252.0.0,60.253.128.0,60.255.0.0,61.4.80.0,61.4.176.0,61.8.160.0,61.28.0.0,61.29.128.0,61.45.128.0,61.47.128.0,61.48.0.0,61.87.192.0,61.128.0.0,61.232.0.0,61.236.0.0,61.240.0.0,114.28.0.0,114.54.0.0,114.60.0.0,114.64.0.0,114.68.0.0,114.80.0.0,116.1.0.0,116.2.0.0,116.4.0.0,116.8.0.0,116.13.0.0,116.16.0.0,116.52.0.0,116.56.0.0,116.58.128.0,116.58.208.0,116.60.0.0,116.66.0.0,116.69.0.0,116.70.0.0,116.76.0.0,116.89.144.0,116.90.184.0,116.95.0.0,116.112.0.0,116.116.0.0,116.128.0.0,116.192.0.0,116.193.16.0,116.193.32.0,116.194.0.0,116.196.0.0,116.198.0.0,116.199.0.0,116.199.128.0,116.204.0.0,116.207.0.0,116.208.0.0,116.212.160.0,116.213.64.0,116.213.128.0,116.214.32.0,116.214.64.0,116.214.128.0,116.215.0.0,116.216.0.0,116.224.0.0,116.242.0.0,116.244.0.0,116.248.0.0,116.252.0.0,116.254.128.0,116.255.128.0,117.8.0.0,117.21.0.0,117.22.0.0,117.24.0.0,117.32.0.0,117.40.0.0,117.44.0.0,117.48.0.0,117.53.48.0,117.53.176.0,117.57.0.0,117.58.0.0,117.59.0.0,117.60.0.0,117.64.0.0,117.72.0.0,117.74.64.0,117.74.128.0,117.75.0.0,117.76.0.0,117.80.0.0,117.100.0.0,117.103.16.0,117.103.128.0,117.106.0.0,117.112.0.0,117.120.64.0,117.120.128.0,117.121.0.0,117.121.128.0,117.121.192.0,117.122.128.0,117.124.0.0,117.128.0.0,118.24.0.0,118.64.0.0,118.66.0.0,118.67.112.0,118.72.0.0,118.80.0.0,118.84.0.0,118.88.32.0,118.88.64.0,118.88.128.0,118.89.0.0,118.91.240.0,118.102.16.0,118.112.0.0,118.120.0.0,118.124.0.0,118.126.0.0,118.132.0.0,118.144.0.0,118.178.0.0,118.180.0.0,118.184.0.0,118.192.0.0,118.212.0.0,118.224.0.0,118.228.0.0,118.230.0.0,118.239.0.0,118.242.0.0,118.244.0.0,118.248.0.0,119.0.0.0,119.2.0.0,119.2.128.0,119.3.0.0,119.4.0.0,119.8.0.0,119.10.0.0,119.15.136.0,119.16.0.0,119.18.192.0,119.18.208.0,119.18.224.0,119.19.0.0,119.20.0.0,119.27.64.0,119.27.160.0,119.27.192.0,119.28.0.0,119.30.48.0,119.31.192.0,119.32.0.0,119.40.0.0,119.40.64.0,119.40.128.0,119.41.0.0,119.42.0.0,119.42.136.0,119.42.224.0,119.44.0.0,119.48.0.0,119.57.0.0,119.58.0.0,119.59.128.0,119.60.0.0,119.62.0.0,119.63.32.0,119.75.208.0,119.78.0.0,119.80.0.0,119.84.0.0,119.88.0.0,119.96.0.0,119.108.0.0,119.112.0.0,119.128.0.0,119.144.0.0,119.148.160.0,119.161.128.0,119.162.0.0,119.164.0.0,119.176.0.0,119.232.0.0,119.235.128.0,119.248.0.0,119.253.0.0,119.254.0.0,120.0.0.0,120.24.0.0,120.30.0.0,120.32.0.0,120.48.0.0,120.52.0.0,120.64.0.0,120.72.32.0,120.72.128.0,120.76.0.0,120.80.0.0,120.90.0.0,120.92.0.0,120.94.0.0,120.128.0.0,120.136.128.0,120.137.0.0,120.192.0.0,121.0.16.0,121.4.0.0,121.8.0.0,121.16.0.0,121.32.0.0,121.40.0.0,121.46.0.0,121.48.0.0,121.51.0.0,121.52.160.0,121.52.208.0,121.52.224.0,121.55.0.0,121.56.0.0,121.58.0.0,121.58.144.0,121.59.0.0,121.60.0.0,121.68.0.0,121.76.0.0,121.79.128.0,121.89.0.0,121.100.128.0,121.101.208.0,121.192.0.0,121.201.0.0,121.204.0.0,121.224.0.0,121.248.0.0,121.255.0.0,122.0.64.0,122.0.128.0,122.4.0.0,122.8.0.0,122.48.0.0,122.49.0.0,122.51.0.0,122.64.0.0,122.96.0.0,122.102.0.0,122.102.64.0,122.112.0.0,122.119.0.0,122.136.0.0,122.144.128.0,122.152.192.0,122.156.0.0,122.192.0.0,122.198.0.0,122.200.64.0,122.204.0.0,122.224.0.0,122.240.0.0,122.248.48.0,123.0.128.0,123.4.0.0,123.8.0.0,123.49.128.0,123.52.0.0,123.56.0.0,123.64.0.0,123.96.0.0,123.98.0.0,123.99.128.0,123.100.0.0,123.101.0.0,123.103.0.0,123.108.128.0,123.108.208.0,123.112.0.0,123.128.0.0,123.136.80.0,123.137.0.0,123.138.0.0,123.144.0.0,123.160.0.0,123.176.80.0,123.177.0.0,123.178.0.0,123.180.0.0,123.184.0.0,123.196.0.0,123.199.128.0,123.206.0.0,123.232.0.0,123.242.0.0,123.244.0.0,123.249.0.0,123.253.0.0,124.6.64.0,124.14.0.0,124.16.0.0,124.20.0.0,124.28.192.0,124.29.0.0,124.31.0.0,124.40.112.0,124.40.128.0,124.42.0.0,124.47.0.0,124.64.0.0,124.66.0.0,124.67.0.0,124.68.0.0,124.72.0.0,124.88.0.0,124.108.8.0,124.108.40.0,124.112.0.0,124.126.0.0,124.128.0.0,124.147.128.0,124.156.0.0,124.160.0.0,124.172.0.0,124.192.0.0,124.196.0.0,124.200.0.0,124.220.0.0,124.224.0.0,124.240.0.0,124.240.128.0,124.242.0.0,124.243.192.0,124.248.0.0,124.249.0.0,124.250.0.0,124.254.0.0,125.31.192.0,125.32.0.0,125.58.128.0,125.61.128.0,125.62.0.0,125.64.0.0,125.96.0.0,125.98.0.0,125.104.0.0,125.112.0.0,125.169.0.0,125.171.0.0,125.208.0.0,125.210.0.0,125.213.0.0,125.214.96.0,125.215.0.0,125.216.0.0,125.254.128.0,134.196.0.0,159.226.0.0,161.207.0.0,162.105.0.0,166.111.0.0,167.139.0.0,168.160.0.0,169.211.1.0,192.83.122.0,192.83.169.0,192.124.154.0,192.188.170.0,198.17.7.0,202.0.110.0,202.0.176.0,202.4.128.0,202.4.252.0,202.8.128.0,202.10.64.0,202.14.88.0,202.14.235.0,202.14.236.0,202.14.238.0,202.20.120.0,202.22.248.0,202.38.0.0,202.38.64.0,202.38.128.0,202.38.136.0,202.38.138.0,202.38.140.0,202.38.146.0,202.38.149.0,202.38.150.0,202.38.152.0,202.38.156.0,202.38.158.0,202.38.160.0,202.38.164.0,202.38.168.0,202.38.176.0,202.38.184.0,202.38.192.0,202.41.152.0,202.41.240.0,202.43.144.0,202.46.32.0,202.46.224.0,202.60.112.0,202.63.248.0,202.69.4.0,202.69.16.0,202.70.0.0,202.74.8.0,202.75.208.0,202.85.208.0,202.90.0.0,202.90.224.0,202.90.252.0,202.91.0.0,202.91.128.0,202.91.176.0,202.91.224.0,202.92.0.0,202.92.252.0,202.93.0.0,202.93.252.0,202.95.0.0,202.95.252.0,202.96.0.0,202.112.0.0,202.120.0.0,202.122.0.0,202.122.32.0,202.122.64.0,202.122.112.0,202.122.128.0,202.123.96.0,202.124.24.0,202.125.176.0,202.127.0.0,202.127.12.0,202.127.16.0,202.127.40.0,202.127.48.0,202.127.112.0,202.127.128.0,202.127.160.0,202.127.192.0,202.127.208.0,202.127.212.0,202.127.216.0,202.127.224.0,202.130.0.0,202.130.224.0,202.131.16.0,202.131.48.0,202.131.208.0,202.136.48.0,202.136.208.0,202.136.224.0,202.141.160.0,202.142.16.0,202.143.16.0,202.148.96.0,202.149.160.0,202.149.224.0,202.150.16.0,202.152.176.0,202.153.48.0,202.158.160.0,202.160.176.0,202.164.0.0,202.164.25.0,202.165.96.0,202.165.176.0,202.165.208.0,202.168.160.0,202.170.128.0,202.170.216.0,202.173.8.0,202.173.224.0,202.179.240.0,202.180.128.0,202.181.112.0,202.189.80.0,202.192.0.0,203.18.50.0,203.79.0.0,203.80.144.0,203.81.16.0,203.83.56.0,203.86.0.0,203.86.64.0,203.88.32.0,203.88.192.0,203.89.0.0,203.90.0.0,203.90.128.0,203.90.192.0,203.91.32.0,203.91.96.0,203.91.120.0,203.92.0.0,203.92.160.0,203.93.0.0,203.94.0.0,203.95.0.0,203.95.96.0,203.99.16.0,203.99.80.0,203.100.32.0,203.100.80.0,203.100.96.0,203.100.192.0,203.110.160.0,203.118.192.0,203.119.24.0,203.119.32.0,203.128.32.0,203.128.96.0,203.130.32.0,203.132.32.0,203.134.240.0,203.135.96.0,203.135.160.0,203.142.219.0,203.148.0.0,203.152.64.0,203.156.192.0,203.158.16.0,203.161.192.0,203.166.160.0,203.171.224.0,203.174.7.0,203.174.96.0,203.175.128.0,203.175.192.0,203.176.168.0,203.184.80.0,203.187.160.0,203.190.96.0,203.191.16.0,203.191.64.0,203.191.144.0,203.192.0.0,203.196.0.0,203.207.64.0,203.207.128.0,203.208.0.0,203.208.16.0,203.208.32.0,203.209.224.0,203.212.0.0,203.212.80.0,203.222.192.0,203.223.0.0,210.2.0.0,210.5.0.0,210.5.144.0,210.12.0.0,210.14.64.0,210.14.112.0,210.14.128.0,210.15.0.0,210.15.128.0,210.16.128.0,210.21.0.0,210.22.0.0,210.23.32.0,210.25.0.0,210.26.0.0,210.28.0.0,210.32.0.0,210.51.0.0,210.52.0.0,210.56.192.0,210.72.0.0,210.76.0.0,210.78.0.0,210.79.64.0,210.79.224.0,210.82.0.0,210.87.128.0,210.185.192.0,210.192.96.0,211.64.0.0,211.80.0.0,211.96.0.0,211.136.0.0,211.144.0.0,211.160.0.0,218.0.0.0,218.56.0.0,218.64.0.0,218.96.0.0,218.104.0.0,218.108.0.0,218.185.192.0,218.192.0.0,218.240.0.0,218.249.0.0,219.72.0.0,219.82.0.0,219.128.0.0,219.216.0.0,219.224.0.0,219.242.0.0,219.244.0.0,220.101.192.0,220.112.0.0,220.152.128.0,220.154.0.0,220.160.0.0,220.192.0.0,220.231.0.0,220.231.128.0,220.232.64.0,220.234.0.0,220.242.0.0,220.248.0.0,220.252.0.0,221.0.0.0,221.8.0.0,221.12.0.0,221.12.128.0,221.13.0.0,221.14.0.0,221.122.0.0,221.129.0.0,221.130.0.0,221.133.224.0,221.136.0.0,221.172.0.0,221.176.0.0,221.192.0.0,221.196.0.0,221.198.0.0,221.199.0.0,221.199.128.0,221.199.192.0,221.199.224.0,221.200.0.0,221.208.0.0,221.224.0.0,222.16.0.0,222.32.0.0,222.64.0.0,222.125.0.0,222.126.128.0,222.128.0.0,222.160.0.0,222.168.0.0,222.176.0.0,222.192.0.0,222.240.0.0,222.248.0.0"

    arr = ips.split(",")
    ip = random.choice(arr)  # 随机选择一个 IP
    return ip


def aes_encrypt(data: str | bytes, key: bytes) -> bytes:
    if isinstance(data, str):
        data = data.encode()
    backend = default_backend()
    cipher = Cipher(algorithms.AES(key), modes.ECB(), backend=backend)  # noqa: S305
    encryptor = cipher.encryptor()
    padder = padding.PKCS7(128).padder()
    padded_data = padder.update(data) + padder.finalize()
    return encryptor.update(padded_data) + encryptor.finalize()


def aes_decrypt(cipher_buffer: bytes, key: bytes) -> bytes:
    backend = default_backend()
    cipher = Cipher(algorithms.AES(key), modes.ECB(), backend=backend)  # noqa: S305
    decryptor = cipher.decryptor()
    unpadder = padding.PKCS7(128).unpadder()
    decrypted_data = decryptor.update(cipher_buffer) + decryptor.finalize()
    return unpadder.update(decrypted_data) + unpadder.finalize()


def eapi_params_encrypt(path: bytes, params: dict) -> str:
    """eapi接口参数加密.

    :param path: url路径
    :param params: 明文参数
    :return str: 请求data.
    """
    params_bytes = json.dumps(params, separators=(",", ":")).encode()
    sign_src = b"nobody" + path + b"use" + params_bytes + b"md5forencrypt"
    sign = hashlib.md5(sign_src).hexdigest()  # noqa: S324
    aes_src = path + b"-36cd479b6b5-" + params_bytes + b"-36cd479b6b5-" + sign.encode()
    encrypted_data = aes_encrypt(aes_src, b"e82ckenh8dichen8")
    return f"params={binascii.hexlify(encrypted_data).upper().decode()}"


def eapi_response_decrypt(cipher_buffer: bytes) -> bytes:
    return aes_decrypt(cipher_buffer, b"e82ckenh8dichen8")


def eapi_request(path: str, params: dict) -> dict:
    encrypted_params = eapi_params_encrypt(path.replace("eapi", "api").encode(), params)
    url = "https://interface3.music.163.com" + path
    response = requests.post(url, headers=headers, data=encrypted_params, timeout=4)
    response.raise_for_status()
    data = eapi_response_decrypt(response.content)
    return json.loads(data)


def get_mp3(ids):
    params = {
        "ids": ids,
        "level": "exhigh",
        "encodeType": "aac",
        "trialMode": "10",
        "immerseType": "aac",
        "cliUserId": "16663700",
        "cliVipTypes": "[1,6]",
        "trialModes": '{"1888915574":10,"393685":10}',
        "supportDolby": "false",
        "volumeBalance": "1",
        "djVolumeBalance": "1",
        "header": "{}",
        "e_r": True,
    }
    data = eapi_request("/eapi/song/enhance/player/url/v1", params=params)
    print(f"data = {data}")
    results = {x.get("id"): x.get("url") for x in data.get("data")}
    return results


singer_detail_cache = {}


def get_singer(id):
    if id in singer_detail_cache:
        return singer_detail_cache[id]
    data = {
        "id": id,
    }
    r = requests.post(
        f"https://netease-cloud-music.malinkang.com/artist/detail?timestamp=f{(time.time()*1000)}",
        data=data,
    )
    if r.ok:
        avatar = (
            r.json()
            .get("data")
            .get("artist")
            .get("avatar")
            .replace("http://", "https://")
        )
        singer_detail_cache[id] = avatar
        return avatar
    return "https://www.notion.so/icons/user-circle-filled_gray.svg"


def get_play_list(id, cookie):
    offset = 0
    limit = 50
    results = []
    while True:
        data = {
            "cookie": cookie,
            "id": id,
            "offset": offset,
            "limit": limit,
        }
        response = requests.post(
            f"https://netease-cloud-music.malinkang.com/playlist/track/all?timestamp=f{int((time.time()*1000))}",
            data=data,
        )
        songs = response.json().get("songs")
        if not songs:  # 如果返回的songs列表为空，跳出循环
            break
        results.extend(songs)  # 将当前请求返回的songs列表添加到results中
        print(f"获取歌曲个数{len(results)}")
        offset += limit  # 更新offset值，准备下一次请求
        return results
    # 将所有获取的数据写入到文件中
    return results


def insert_music(tracks, playlist_database_id):
    for index, track in enumerate(tracks):
        print(
            f"正在插入{ track.get('name')}，一共{len(tracks)}首，当前是第{index+1}首。"
        )
        item = {}
        item["歌曲"] = track.get("name")
        item["URL"] = track.get("url")
        item["Id"] = str(track.get("id"))
        item["歌手"] = [
            notion_helper.get_relation_id(
                x.get("name"),
                notion_helper.singer_database_id,
                get_icon(get_singer(x.get("id"))),
                {"id": {"number": x.get("id")}},
            )
            for x in track.get("ar")
        ]
        # al对象存储专辑数据
        al = track.get("al")
        item["专辑"] = [
            notion_helper.get_relation_id(
                al.get("name"),
                notion_helper.album_database_id,
                get_icon(al.get("picUrl")),
                {"id": {"number": al.get("id")}},
            )
        ]
        item["歌单"] = [playlist_database_id]
        item["日期"] = pendulum.now().int_timestamp
        properties = utils.get_properties(item, song_properties_type_dict)
        parent = {
            "database_id": notion_helper.song_database_id,
            "type": "database_id",
        }
        # 暂时拿不到歌曲添加到歌单的时间就拿当前时间吧。
        notion_helper.get_date_relation(properties, pendulum.now(tz="Asia/Shanghai"))
        # Notion竟然不支持http的图？
        notion_helper.create_page(
            parent=parent,
            properties=properties,
            icon=get_icon(track.get("al").get("picUrl").replace("http://", "https://")),
        )


def get_playlist_detail(id):
    data = {
        "cookie": cookie,
        "id": id,
    }
    response = requests.post(
        f"https://netease-cloud-music.malinkang.com/playlist/detail?timestamp=f{int((time.time()*1000))}",
        data=data,
    )
    return response.json().get("playlist")


def login(phone, password):
    """登录"""
    data = {
        "phone": phone,
        "password": password,
    }
    response = requests.post(
        "https://netease-cloud-music.malinkang.com/login/cellphone", data=data
    )
    if response.ok:
        return response.json().get("cookie")
    else:
        print(f"login failed {response.text}")


if __name__ == "__main__":
    notion_helper = NotionHelper()
    # auth = HTTPBasicAuth(f"{os.getenv('PHONE').strip()}", f"{os.getenv('PASSWORD').strip()}")
    # phone = os.getenv('PHONE').strip()
    # password = os.getenv('PASSWORD').strip()
    # if phone and password:
    #     cookie = login(phone,password)
    cookie = os.getenv("COOKIE").strip()
    headers["cookie"] = cookie
    ip = cnip()
    if ip:
        headers["X-Real-IP"] = ip
        headers["X-Forwarded-For"] = ip
    playlist_id = 13176243
    songs = notion_helper.query_all(database_id=notion_helper.song_database_id)
    print(f"从Notion中获取{len(songs)}首")
    # for index,song in enumerate(songs):
    #     notion_helper.delete_block(song.get("id"))
    #     print(f"一共{len(songs)}条，正在删除第{index}条")
    # # 获取歌单详情
    playlist = get_playlist_detail(playlist_id)
    playlist_name = playlist.get("name")
    playlist_cover = playlist.get("coverImgUrl")
    playlist_database_id = notion_helper.get_relation_id(
        playlist_name, notion_helper.playlist_database_id, get_icon(playlist_cover)
    )
    ids = [utils.get_property_value(song.get("properties").get("Id")) for song in songs]
    songs = get_play_list(playlist_id, cookie)
    songs = [item for item in songs if str(item["id"]) not in ids]
    songs = list(reversed(songs))
    ids = [str(item.get("id")) for item in songs]
    ids = formatted_str = json.dumps(ids)
    urls = get_mp3(ids)
    for song in songs:
        if song.get("id") in urls:
            song["url"] = urls.get(song.get("id"))
    insert_music(songs, playlist_database_id)
