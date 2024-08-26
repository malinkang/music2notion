import os
import json
from requests.auth import HTTPBasicAuth
import pendulum
from retrying import retry
import requests
from notion_helper import NotionHelper
import utils
import time

from config import song_properties_type_dict, USER_ICON_URL
from utils import get_icon, split_emoji_from_string
from dotenv import load_dotenv

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
    for track in tracks:
        item = {}
        item["歌曲"] = track.get("name")
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
        item["日期"] = pendulum.now(tz="Asia/Shanghai").int_timestamp
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


def login():
    """登录"""
    data = {
        "phone": os.getenv("PHONE").strip(),
        "password": os.getenv("PASSWORD").strip(),
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

    # auth = HTTPBasicAuth(f"{os.getenv('EMAIL').strip()}", f"{os.getenv('PASSWORD').strip()}")
    # insert_to_notion()
    # email = os.getenv('EMAIL').strip()
    # password = os.getenv('PASSWORD').strip()
    # if os.path.isfile("cookie"):
    #     print("cookie file exists")
    # if email and password:
    #     cookie = login()
    cookie = os.getenv("COOKIE").strip()
    playlist_id = 13176243
    songs = notion_helper.query_all(database_id=notion_helper.song_database_id)
    print(f"从Notion中获取{len(songs)}首")
    # 获取歌单详情
    playlist = get_playlist_detail(playlist_id)
    playlist_name = playlist.get("name")
    playlist_cover = playlist.get("coverImgUrl")
    playlist_database_id = notion_helper.get_relation_id(
        playlist_name, notion_helper.playlist_database_id, get_icon(playlist_cover)
    )
    ids = [utils.get_property_value(song.get("properties").get("Id")) for song in songs]
    songs = get_play_list(playlist_id, cookie)
    songs = [item for item in songs if item["id"] not in ids]
    insert_music(songs, playlist_database_id)
