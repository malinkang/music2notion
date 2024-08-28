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
    # 将所有获取的数据写入到文件中
    return results


def insert_music(tracks, playlist_database_id):
    for index, track in enumerate(tracks):
        print(f"正在插入{ track.get('name')}，一共{len(tracks)}首，当前是第{index+1}首。")
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
    playlist_id = 13176243
    songs = notion_helper.query_all(database_id=notion_helper.song_database_id)
    print(f"从Notion中获取{len(songs)}首")
    for index,song in enumerate(songs):
        notion_helper.delete_block(song.get("id"))
        print(f"一共{len(songs)}条，正在删除第{index}条")
    # # 获取歌单详情
    # playlist = get_playlist_detail(playlist_id)
    # playlist_name = playlist.get("name")
    # playlist_cover = playlist.get("coverImgUrl")
    # playlist_database_id = notion_helper.get_relation_id(
    #     playlist_name, notion_helper.playlist_database_id, get_icon(playlist_cover)
    # )
    # ids = [utils.get_property_value(song.get("properties").get("Id")) for song in songs]
    # songs = get_play_list(playlist_id, cookie)
    # songs = [item for item in songs if str(item["id"]) not in ids]
    # songs = list(reversed(songs))
    # ids = [str(item.get("id")) for item in songs]
    # ids = formatted_str = json.dumps(ids)
    # urls = get_mp3(ids)
    # for song in songs:
    #     if song.get("id") in urls:
    #         song["url"] = urls.get("id")
    # insert_music(songs, playlist_database_id)
