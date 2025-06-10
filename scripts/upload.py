import os
import requests
import json
import time
import hashlib
from typing import Dict, Any, Optional
#https://openapi.alipan.com/oauth/authorize?client_id=6e1825e239d84170835e58e68b4c38fd&redirect_uri=https://alipan.notionhub.app/auth-callback&scope=user:base,file:all:read,file:all:write&style=folder
class AliyunDriveUploader:
    """阿里云盘文件上传类"""
    
    BASE_URL = "https://openapi.alipan.com"
    
    def __init__(self, access_token: str):
        """
        初始化上传器
        
        Args:
            refresh_token: 阿里云盘的刷新令牌
        """
        self.refresh_token = access_token
        self.access_token = access_token
        self.drive_id = None
        self.user_id = None
        self.folder_id = None
        self.get_user_info()
        self._refresh_access_token()

    def get_file(self, file_id: str) -> Dict[str, Any]:
        """
        获取文件详情
        
        Args:
            file_id: 文件ID
            fields: 指定返回哪些字段，逗号分隔，如 'id_path,name_path'
            
        Returns:
            包含文件详情的字典
        """
        url = f"{self.BASE_URL}/adrive/v1.0/openFile/getDownloadUrl"
        payload = {
            "drive_id": self.drive_id,
            "file_id": file_id
        }
        
            
        response = requests.post(url, headers=self._get_headers(), json=payload)
        print(response.text)
        if response.status_code != 200:
            raise Exception(f"获取文件详情失败: {response.text}")
        
        return response.json()

        # 添加获取用户信息的方法
    def get_user_info(self) -> Dict[str, Any]:
        """
        获取用户信息
        
        Returns:
            包含用户信息的字典
        """
        url = f"{self.BASE_URL}/oauth/users/info"
        print(url)
        response = requests.get(url, headers=self._get_headers())
        print(response.json())
        if response.status_code != 200:
            raise Exception(f"获取用户信息失败: {response.text}")
        
        return response.json()
    
    def _refresh_access_token(self) -> None:
        """刷新访问令牌"""
        url = f"{self.BASE_URL}/adrive/v1.0/user/getDriveInfo"
        
        response = requests.post(url,headers=self._get_headers())
        print(response.status_code)
        if response.status_code != 200:
            raise Exception(f"刷新令牌失败: {response.text}")
        data = response.json()
        print(data)
        self.drive_id = data.get("default_drive_id")
        self.user_id = data.get("user_id")
        self.folder_id = data.get("folder_id")
        print(self.drive_id)
    
    def _get_headers(self) -> Dict[str, str]:
        """获取请求头"""
        return {
            "Authorization": f"Bearer {self.access_token}",
            "Content-Type": "application/json"
        }
    
    def create_folder(self, folder_name: str, parent_id: str = "root") -> str:
        """
        创建文件夹
        
        Args:
            folder_name: 文件夹名称
            parent_id: 父文件夹ID，默认为根目录
            
        Returns:
            文件夹ID
        """
        url = f"{self.BASE_URL}/v2/file/create"
        payload = {
            "drive_id": self.drive_id,
            "parent_file_id": parent_id,
            "name": folder_name,
            "type": "folder",
            "check_name_mode": "auto_rename"
        }
        
        response = requests.post(url, headers=self._get_headers(), json=payload)
        if response.status_code != 201:
            raise Exception(f"创建文件夹失败: {response.text}")
        
        return response.json().get("file_id")
    
    def upload_file(self, file_path: str) -> Dict[str, Any]:
        """
        上传文件
        
        Args:
            file_path: 本地文件路径
            parent_id: 父文件夹ID，默认为根目录
            
        Returns:
            上传成功后的文件信息
        """
        file_name = os.path.basename(file_path)
        file_size = os.path.getsize(file_path)
        
        # 1. 创建上传任务
        create_result = self._create_file(file_name, file_size)
        upload_id = create_result.get("upload_id")
        file_id = create_result.get("file_id")
        
        # 2. 获取上传URL
        part_info_list = create_result.get("part_info_list", [])
        
        # 3. 上传文件分片
        with open(file_path, "rb") as f:
            for part in part_info_list:
                part_number = part.get("part_number")
                upload_url = part.get("upload_url")
                
                # 计算分片大小
                if part_number < len(part_info_list):
                    content_size = 10 * 1024 * 1024  # 10MB
                else:
                    content_size = file_size - (part_number - 1) * 10 * 1024 * 1024
                
                content = f.read(content_size)
                
                # 上传分片
                response = requests.put(upload_url, data=content)
                if response.status_code != 200:
                    raise Exception(f"上传分片失败: {response.text}")
        
        # 4. 完成上传
        complete_result = self._complete_upload(file_id, upload_id)
        return complete_result
    
    def _create_file(self, file_name: str, file_size: int) -> Dict[str, Any]:
        """创建文件上传任务"""
        url = f"{self.BASE_URL}/adrive/v1.0/openFile/create"
        
        # 计算分片数量
        part_count = (file_size + 10 * 1024 * 1024 - 1) // (10 * 1024 * 1024)
        part_info_list = [{"part_number": i + 1} for i in range(part_count)]
        
        payload = {
            "drive_id": self.drive_id,
            "parent_file_id": self.folder_id,
            "name": file_name,
            "type": "file",
            "size": file_size,
            "check_name_mode": "auto_rename",
            "part_info_list": part_info_list
        }
        
        response = requests.post(url, headers=self._get_headers(), json=payload)
        print(response.text)
        print(response.status_code)
        if not response.ok:
            raise Exception(f"创建上传任务失败: {response.text}")
        
        return response.json()
    
    def _complete_upload(self, file_id: str, upload_id: str) -> Dict[str, Any]:
        """完成文件上传"""
        url = f"{self.BASE_URL}/adrive/v1.0/openFile/complete"
        payload = {
            "drive_id": self.drive_id,
            "file_id": file_id,
            "upload_id": upload_id
        }
        
        response = requests.post(url, headers=self._get_headers(), json=payload)
        # 将结果写入complete.json文件
        with open('complete.json', 'w', encoding='utf-8') as f:
            json.dump(response.json(), f, ensure_ascii=False, indent=2)
        if response.status_code != 200:
            raise Exception(f"完成上传失败: {response.text}")
        
        return response.json()

def upload_to_aliyun_drive(file_path: str, refresh_token: str, parent_folder: Optional[str] = None) -> Dict[str, Any]:
    """
    上传文件到阿里云盘
    
    Args:
        file_path: 要上传的文件路径
        refresh_token: 阿里云盘的刷新令牌
        parent_folder: 上传到的文件夹名称，如果不存在则创建
        
    Returns:
        上传成功后的文件信息
    """
    uploader = AliyunDriveUploader(refresh_token)
    
    # 如果指定了父文件夹，则创建或获取文件夹ID
    parent_id = "root"
    if parent_folder:
        parent_id = uploader.create_folder(parent_folder)
    
    # 上传文件
    result = uploader.upload_file(file_path, parent_id)
    return result
# 示例用法
code = "授权码"  # 从重定向URL中获取的授权码
client_id = "你的应用ID"
client_secret = "你的应用密钥"
redirect_uri = "你的重定向URI"

# 添加获取 access_token 的函数
#https://www.yuque.com/aliyundrive/zpfszx/efabcs#Fyis9

# {
#   "token_type": "Bearer",
#   "access_token": "eyJraWQiOiJLcU8iLCJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9.eyJzdWIiOiI0Y2QwZjhmNzA4MDc0Njg3YWE4MjJmNDU5YTY2ZDZmNyIsImF1ZCI6IjZlMTgyNWUyMzlkODQxNzA4MzVlNThlNjhiNGMzOGZkIiwicyI6ImNhIiwiZCI6IjIyMjI0Mzk2MzA6NjcxYTMwZmY5NTVmM2I1NzZkNmU0M2UxYjU1MWRhYzQ2MjAyNTk4MiIsImlzcyI6ImFsaXBhbiIsImV4cCI6MTc0MTI1NDYzNywiaWF0IjoxNzQxMjQ3NDM0LCJqdGkiOiI4MTAwZTZiZWRiNzY0MjgyYWQyOTliZjFlMGNlNTk4YyJ9.NdWQD3669asaM7f4_ZgMbNAT69A800CsleThaYk2Nis",
#   "refresh_token": "eyJ0eXAiOiJKV1QiLCJhbGciOiJSUzI1NiJ9.eyJzdWIiOiI0Y2QwZjhmNzA4MDc0Njg3YWE4MjJmNDU5YTY2ZDZmNyIsImF1ZCI6IjZlMTgyNWUyMzlkODQxNzA4MzVlNThlNjhiNGMzOGZkIiwiZXhwIjoxNzQ5MDIzNDM0LCJpYXQiOjE3NDEyNDc0MzQsImp0aSI6ImM3M2MzZjNkMWZiYTRiNmI5NTA4M2JhN2E5ZDlmYjE1In0.GK2ot1bnKplNSiMxinRXzFDQHJ2BQKcD7asOGcnYStWH8o_rsXtFTvUNuS7tzkFSZ5RJgq3vCeVJMBc_Brq4Mw",
#   "expires_in": 7200
# }
def get_access_token_by_code(code: str, client_id: str, client_secret: str, redirect_uri: str) -> Dict[str, Any]:
    """
    通过授权码获取访问令牌
    
    Args:
        code: 授权码
        client_id: 应用ID
        client_secret: 应用密钥
        redirect_uri: 重定向URI
        
    Returns:
        包含 access_token, refresh_token 等信息的字典
    """
    url = "https://openapi.alipan.com/oauth/access_token"
    payload = {
        "code": code,
        "grant_type": "authorization_code",
        "client_id": client_id,
        "client_secret": client_secret,
        "redirect_uri": redirect_uri
    }
    
    response = requests.post(url, json=payload)
    if response.status_code != 200:
        raise Exception(f"获取访问令牌失败: {response.text}")
    
    return response.json()

if __name__ == "__main__":
    client_id = "6e1825e239d84170835e58e68b4c38fd"
    client_secret = "839482d40fa1420993e82c5c9818055d"
    redirect_uri = "https://malinkang.com"
    # code = "a946df4a6bed4ea2953e7e88d1426845"
    # try:
    #     token_info = get_access_token_by_code(code, client_id, client_secret, redirect_uri)
    #     print(f"获取令牌成功: {json.dumps(token_info, ensure_ascii=False, indent=2)}")
        
    #     # 使用获取到的 refresh_token 上传文件
    #     refresh_token = token_info.get("refresh_token")
    #     result = upload_to_aliyun_drive("要上传的文件路径", refresh_token, "可选的目标文件夹")
    #     print(f"文件上传成功: {json.dumps(result, ensure_ascii=False, indent=2)}")
    # except Exception as e:
    #     print(f"操作失败: {str(e)}")
    # 示例用法
    # import argparse
    
    # parser = argparse.ArgumentParser(description="上传文件到阿里云盘")
    # parser.add_argument("file_path", help="要上传的文件路径")
    # parser.add_argument("--token", required=True, help="阿里云盘的刷新令牌")
    # parser.add_argument("--folder", help="上传到的文件夹名称，如果不存在则创建")
    
    # args = parser.parse_args()
    access_token = "eyJraWQiOiJLcU8iLCJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9.eyJzdWIiOiI0Y2QwZjhmNzA4MDc0Njg3YWE4MjJmNDU5YTY2ZDZmNyIsImF1ZCI6IjZlMTgyNWUyMzlkODQxNzA4MzVlNThlNjhiNGMzOGZkIiwicyI6ImNkYSIsImQiOiIyMjIyNDM5NjMwOjY3Yzk4MjU1MWU0ZGJlNDdlMTk3NDc4ODkxYWViNjhmZDZlNzdmZTMiLCJpc3MiOiJhbGlwYW4iLCJleHAiOjE3NDEyNjgxMTMsImlhdCI6MTc0MTI2MDkxMCwianRpIjoiZmYyMjk2M2E5ZTBmNGM0MTliMDhlMTY4MDdlMTAyOWIifQ.zWwtEyOfGli9O1VYgigyhnIHdcxgN_5aLHU6jaBOnZE"
    uploader = AliyunDriveUploader(access_token)
    # uploader.upload_file("a.mp3")
    uploader.get_file("67c9897c214d609dd8bf469689b7368e7d209e43")
    # file_path = ""
    # folder = "music"
    # try:
    #     result = upload_to_aliyun_drive(file_path, token, folder)
    #     print(f"文件上传成功: {json.dumps(result, ensure_ascii=False, indent=2)}")
    # except Exception as e:
    #     print(f"上传失败: {str(e)}")