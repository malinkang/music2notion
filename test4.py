from urllib.parse import urlparse

def remove_query_string(url):
    # 解析 URL
    parsed_url = urlparse(url)
    # 重新构建 URL，不包括查询字符串
    cleaned_url = parsed_url._replace(query='').geturl()
    return cleaned_url

# 示例链接
url = "http://m804.music.126.net/20240829114300/2c20e2f734c8909545e2c7a7b66589c5/jdyyaac/obj/w5rDlsOJwrLDjj7CmsOj/14096414354/9193/ebb9/48fa/2ad1be7a9d8501702aefba19e73dff74.m4a?authSecret=000001919c23d99d10800a3b201700b5"
cleaned_url = remove_query_string(url)

print(cleaned_url)