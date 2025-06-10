
import os
import pendulum
from pyncm.apis.track import GetTrackAudio
import requests
from notion_helper import NotionHelper
from dotenv import load_dotenv
from config import song_properties_type_dict, USER_ICON_URL
from upload2 import NotionFileUploader
from utils import get_icon, get_properties,get_property_value
load_dotenv()
from pyncm.apis.login import (
    LoginViaCookie,
)
from pyncm.apis.playlist import (
    GetPlaylistAllTracks
)
from pyncm.apis.artist import (
    GetArtistDetails
)
from pyncm.apis.track import (
    GetTrackLyrics
)

def get_artist_avatar(id):
    return GetArtistDetails(id).get("data").get("artist").get("avatar")

def get_track_audio(ids):
    return GetTrackAudio(song_ids=ids, bitrate=3200 * 1000)

def download(url, name):
    if url:
        response = requests.get(url)
        print(response.text)
        if response.ok:
            extension  = "mp3"
            # # 处理扩展名，去掉?及其后面的内容
            # if '.' in url:
            #     extension = url.split('.')[-1]
            #     if '?' in extension:
            #         extension = extension.split('?')[0]
            # else:
            #     extension = 'unknown'
            file_name = f"{name}.{extension}"
            with open(file_name, 'wb') as f:
                f.write(response.content)
            file_size_kb = os.path.getsize(file_name) / 1024
            print(f"{name} 下载成功，保存为 {file_name}，文件大小为 {file_size_kb:.2f} KB")
            return file_name
        else:
            print(f"Failed to download {name} from {url}")
def insert_music(tracks):
    for index, track in enumerate(tracks):
        print(
            f"正在插入{ track.get('name')}，一共{len(tracks)}首，当前是第{index+1}首。"
        )
        item = {}
        item["歌曲"] = track.get("name")
        item["Id"] = str(track.get("id"))
        item["平台"] = "网易云音乐"
        item["歌手"] = [
            notion_helper.get_relation_id(
                x.get("name"),
                notion_helper.singer_database_id,
                get_icon(get_artist_avatar(x.get("id"))),
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
        # item["歌单"] = [playlist_database_id]
        item["日期"] = pendulum.now().int_timestamp
        properties = get_properties(item, song_properties_type_dict)
        parent = {
            "database_id": notion_helper.song_database_id,
            "type": "database_id",
        }
        # 暂时拿不到歌曲添加到歌单的时间就拿当前时间吧。
        notion_helper.get_date_relation(properties, pendulum.now(tz="Asia/Shanghai"))
        # Notion竟然不支持http的图？
        cover = track.get("al").get("picUrl").replace("http://", "https://")
     
        result =notion_helper.create_page(
            parent=parent,
            properties=properties,
            cover=get_icon(cover),
            icon=get_icon(cover),
        )
        file_name = download(track.get("url"), track.get("name"))
        uploader.upload_file_to_database_property(file_name,result.get("id"),"音频")
        lyrics_file_name = get_lyrics(track.get("id"), track.get("name"))
        uploader.upload_file_to_database_property(lyrics_file_name,result.get("id"),"歌词")

def get_lyrics(song_id: str, file_name: str) -> str:
    """
    调用GetTrackLyricsNew获取歌词并保存到本地文件，返回文件名

    参数:
        song_id (str): 歌曲ID
        file_name (str): 文件名（不带扩展名）

    返回:
        str: 保存后的本地文件名（带.txt扩展名）
    """
    import re
    # 调用GetTrackLyricsNew获取歌词
    lyrics_data = GetTrackLyrics(song_id)
    # 将结果写入到json文件
    import json
    safe_file_name = re.sub(r'[\\/:*?"<>|]', '_', file_name)
    json_file_name = f"{safe_file_name}_lyrics.json"
    with open(json_file_name, "w", encoding="utf-8") as jf:
        json.dump(lyrics_data, jf, ensure_ascii=False, indent=2)
    # 兼容网易云歌词结构
    lyrics = ""
    if lyrics_data and isinstance(lyrics_data, dict):
        if "lrc" in lyrics_data and "lyric" in lyrics_data["lrc"]:
            lyrics = lyrics_data["lrc"]["lyric"]
        elif "lyric" in lyrics_data:
            lyrics = lyrics_data["lyric"]
        else:
            lyrics = str(lyrics_data)
    else:
        lyrics = "未获取到歌词"
    # 确保文件名安全
    safe_file_name = re.sub(r'[\\/:*?"<>|]', '_', file_name)
    full_file_name = f"{safe_file_name}.json"
    with open(full_file_name, "w", encoding="utf-8") as f:
        f.write(lyrics)
    return full_file_name


if __name__ == "__main__":
    notion_helper = NotionHelper()
    uploader = NotionFileUploader()
    songs = notion_helper.query_all(notion_helper.song_database_id)
    song_ids = [get_property_value(song.get("properties").get("Id")) for song in songs]
    LoginViaCookie(MUSIC_U=os.getenv("COOKIE"))
    songs = GetPlaylistAllTracks("13176243").get("songs")
    print(len(songs))
    songs = [song for song in songs if str(song.get("id")) not in song_ids]
    print(len(songs))
    data = get_track_audio([song.get("id") for song in songs]).get("data")
    data = {x.get("id"): x.get("url") for x in data}
    for song in songs:
        if song.get("id") in data:
            song["url"] = data[song.get("id")]
    insert_music(songs)

