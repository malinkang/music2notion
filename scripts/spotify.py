import base64
import json
import requests

# 设置你的Spotify API密钥
CLIENT_ID = "f72510c0037042c5bb7b64066db4db15"
CLIENT_SECRET = "b8f656f28a11477f93b6cda13808eba7"
REIRECT_URL = "https://malinkang.com/"
code = "AQAnTleU9p_iz9G_56zrrtpZyWDRMGxCAr5s3Aj9htprTkAGARB4BWyjPa-OELZgy0OhkOXAU_2Y8HYvpuWpz6L2uucAhyzvXFfPs6nlFGsFP9ZGJJA_grx6OezLaza04z13F4fojMXmSqqnGAepOI1pON3Fw6PImCzXZZ47IGj3LpItpKEeFimsk7ZFk9Ty88H3C5fQh3uDrhILYn-KTvDqv9gvlQMmi1bFIN6_inro"
def get_token():
    # 设置请求参数
    url = "https://accounts.spotify.com/api/token"
    headers = {
        "Content-Type": "application/x-www-form-urlencoded",
        "Authorization":"Basic " +string_to_base64(CLIENT_ID+":"+CLIENT_SECRET)
    }
    data = {
        "code":code,
        "grant_type": "authorization_code",
        "redirect_uri": f"{REIRECT_URL}",
    }

    # 发送POST请求
    response = requests.post(url, headers=headers, data=data)
    print(response.text)
    return response.json().get("access_token")


def get_artist(artist_id, token):
    url = f"https://api.spotify.com/v1/artists/{artist_id}"
    headers = {
        "Authorization": f"Bearer {token}"
    }
    response = requests.get(url, headers=headers)
    return response.json()

def get_liked_songs(token):
    print(token)
    url = "https://api.spotify.com/v1/me/tracks"
    headers = {
        "Authorization": f"Bearer {token}"
    }
    response = requests.get(url, headers=headers)
    print(response.text)
    return response.json()
def string_to_base64(input_string):
    # 将字符串编码为bytes
    input_bytes = input_string.encode('utf-8')

    # 使用base64进行编码
    encoded_bytes = base64.b64encode(input_bytes)

    # 将编码后的bytes转换为字符串
    encoded_string = encoded_bytes.decode('utf-8')

    return encoded_string

if __name__ == "__main__":
    # get_token()
        # 调用方法并将结果写入到artist.json中
    artist_id = "4Z8W4fKeB5YxbusRsdQVPb"
    # token = get_token()
    # token = "QDgHoDTbdCCM_Xyn6BE6IRPB1PmjRnlt1UTUxBh2zt1tyoposUeBHabtHMpCDyEqmF1jzHOuzy4DsfHmdKICQRs4P9-2TXtUeJKm6V0B8Yku83_cLjOHeNoYwsp0_nvibIwqCCPAbETZY4ryLJMAufQrIypmS-goZLnfpUG722Ob-YWJBBMIRdK9dPamhVQObIaHIbYblRHXw"
    # token2="QBGNy_sl8h6_LrxxF04TjgNdsohJdZZw8ChGePmGgq2YkvWaWzdCXmJXnODJob8haD-0gXitNJC56seZ0a_NtHztHlc3NJmU3rsoL7k3hj9c2VDtG3-R8Piu_yyGzbIPko"
    # token = "BQCBC5IOByNLX1UZfJXQlUqJ0PuOIthcmI0IfjCtCuBKNJMagAEZP668cF8Nd--TzmjKXspPcty1FoaQb5ISDv5eklFEWOg1fTr_Erg6_MpgH7dADvo"
    result = get_liked_songs( get_token())

    with open('artist.json', 'w') as f:
        json.dump(result, f)
# end main



