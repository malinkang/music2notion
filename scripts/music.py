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
from urllib.parse import urlparse
from PIL import Image
import io
def remove_query_string(url):
    # 解析 URL
    parsed_url = urlparse(url)
    # 重新构建 URL，不包括查询字符串
    cleaned_url = parsed_url._replace(query='').geturl()
    return cleaned_url
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
    results = {x.get("id"): remove_query_string(x.get("url")) for x in data.get("data")}
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
        item["平台"] = "网易云音乐"
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
        cover = track.get("al").get("picUrl").replace("http://", "https://")
        notion_helper.create_page(
            parent=parent,
            properties=properties,
            cover=get_icon(cover),
            icon=get_icon(cover),
        )
        file = download(track.get("url"),track.get("name"))
        cover = download(track.get("al").get("picUrl"),track.get("name"))
        # lyric = get_lyric(track.get("id"))
        
        send(file,cover,track.get("name"),"&".join([x.get("name") for x in track.get("ar")])
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
        return response.json()
    else:
        print(f"login failed {response.text}")

def get_like_playlist(uid,nickname):
    """获取我喜欢的音乐id"""
    response = requests.post(
        f"https://netease-cloud-music.malinkang.com/user/playlist?uid={uid}",headers=headers
    )
    if response.ok:
        playlist =  response.json().get("playlist")
        playlist_name = f"{nickname}喜欢的音乐"
        playlist = [x for x in playlist if x.get("name")==playlist_name]
        playlist = sorted(playlist, key=lambda x: x['createTime'])
        if playlist:
            return playlist[0].get("id")
    else:
        print(f"get failed {response.text}")
        
def get_lyric(id):
    """获取歌词，并保存到文件中"""
    response = requests.get(
        f"https://netease-cloud-music.malinkang.com/lyric?id={id}", headers=headers
    )
    if response.ok:
        lyrics = response.json().get("lrc", {}).get("lyric", "")
        return lyrics
    else:
        print(f"获取歌词失败 {response.text}")

def download(url,name):
    if url:
        response = requests.get(url)
        if response.ok:
            extension = url.split('.')[-1] if '.' in url else 'unknown'
            file_name = f"{name}.{extension}"
            with open(file_name, 'wb') as f:
                f.write(response.content)
            file_size_kb = os.path.getsize(file_name) / 1024
            print(f"{name} 下载成功，保存为 {file_name}，文件大小为 {file_size_kb:.2f} KB")
            return file_name
        else:
            print(f"Failed to download {name} from {url}")
def compress_thumb(cover_path, max_size_kb=200, max_dim=320):
    """压缩图片作为Telegram缩略图"""
    # 检查原始文件大小
    original_size = os.path.getsize(cover_path)
    if original_size <= max_size_kb * 1024:
        with open(cover_path, 'rb') as f:
            return io.BytesIO(f.read())
    
    # 原图过大，需要压缩
    img = Image.open(cover_path)
    
    # 如果图片模式是RGBA，转换为RGB
    if img.mode in ('RGBA', 'P'):
        img = img.convert('RGB')
    
    # 调整尺寸
    width, height = img.size
    if width > max_dim or height > max_dim:
        ratio = min(max_dim/width, max_dim/height)
        new_size = (int(width*ratio), int(height*ratio))
        img = img.resize(new_size, Image.Resampling.LANCZOS)
    
    # 压缩图片
    buffer = io.BytesIO()
    quality = 95
    img.save(buffer, format='JPEG', quality=quality)
    
    # 如果大小超过限制，逐步降低质量直到满足要求
    while buffer.tell() > max_size_kb * 1024 and quality > 10:
        buffer.seek(0)
        buffer.truncate()
        quality -= 5
        img.save(buffer, format='JPEG', quality=quality)
    
    buffer.seek(0)
    return buffer

def send(audio,cover,title, performer):
    # 配置信息
    BOT_TOKEN = "5509900379:AAHSimr7FiKrclApJImy91A3Dff4R4g2OPk"  # 替换为你的 Bot Token
    CHAT_ID = "902643712"  # 替换为频道的 Chat ID

    # 构造请求 URL
    url = f"https://api.telegram.org/bot{BOT_TOKEN}/sendAudio"

    # 上传音频文件
    with open(audio, 'rb') as audio_file:
        thumb_buffer = compress_thumb(cover)
        response = requests.post(
            url,
            data={"chat_id": CHAT_ID, 'title': title,'performer': performer  },
            files={"audio": audio_file, 'thumb': ('thumb.jpg', thumb_buffer, 'image/jpeg')}
        )
    # 检查结果
    if response.status_code == 200:
        print("音频文件发送成功！")
    else:
        print(f"发送失败，错误信息: {response.text}")


if __name__ == "__main__":
    notion_helper = NotionHelper()
    auth = HTTPBasicAuth(f"{os.getenv('PHONE').strip()}", f"{os.getenv('PASSWORD').strip()}")
    # phone = os.getenv('PHONE').strip()
    # password = os.getenv('PASSWORD').strip()
    # if phone and password:
    # user_info = login(phone,password)
    uid = "16663700"
    nickname = "malinkang"
    cookie = os.getenv('COOKIE')
    headers["cookie"] = cookie
    playlist_id = get_like_playlist(uid,nickname)
    playlist = get_playlist_detail(playlist_id)
    playlist_name = playlist.get("name")
    playlist_cover = playlist.get("coverImgUrl")
    playlist_database_id = notion_helper.get_relation_id(
        playlist_name, notion_helper.playlist_database_id, get_icon(playlist_cover)
    )
    songs = notion_helper.query_all(notion_helper.song_database_id)
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
