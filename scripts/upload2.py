import requests
import os
import mimetypes
import json # 用于美化打印JSON
from dotenv import load_dotenv
load_dotenv()
class NotionFileUploader:
    """
    一个用于将文件上传到 Notion 的类。
    支持单部分和多部分文件上传，并将文件作为块附加到 Notion 页面或现有块，
    或更新数据库页面的文件属性。
    """

    MAX_SINGLE_PART_UPLOAD_SIZE = 20 * 1024 * 1024 # 20 MB

    def __init__(self, notion_version: str = "2022-06-28"):
        """
        初始化 NotionFileUploader 实例。

        Args:
            notion_token (str): 你的 Notion 集成令牌。
            notion_version (str): Notion API 版本。默认为 "2022-06-28"。
        """
        self.notion_token = os.getenv("NOTION_TOKEN")
        self.headers = {
            "Authorization": f"Bearer {self.notion_token}",
            "Notion-Version": notion_version,
            "Content-Type": "application/json" # 默认设置 Content-Type
        }
        self.base_url = "https://api.notion.com/v1"

    def upload_file(self, file_path: str, parent_id: str, parent_type: str = "page_id"):
        """
        将文件上传到 Notion 并将其附加到指定的父级（页面或块）。

        Args:
            file_path (str): 要上传的文件的路径。
            parent_id (str): 要附加文件的父级（页面或块）的 ID。
            parent_type (str): "page_id" 或 "block_id"，取决于要附加到的位置。
                               如果附加到数据库属性，请使用 upload_file_to_database_property 方法。

        Returns:
            dict: 上传文件的 Notion API 响应或错误消息。
        """
        if not os.path.exists(file_path):
            return {"error": f"文件未找到：{file_path}"}

        file_size = os.path.getsize(file_path)
        file_name = os.path.basename(file_path)
        content_type, _ = mimetypes.guess_type(file_path)
        if content_type is None:
            content_type = "application/octet-stream"

        print(f"准备上传文件：'{file_name}'，大小：{file_size / (1024 * 1024):.2f} MB")

        if file_size <= self.MAX_SINGLE_PART_UPLOAD_SIZE:
            print(f"文件大小 <= {self.MAX_SINGLE_PART_UPLOAD_SIZE / (1024 * 1024):.0f} MB，执行单部分上传。")
            # 单部分上传后直接调用 attach_uploaded_file，因为这是针对 block 的
            file_upload_result = self._single_part_upload_content(file_path, file_name, content_type)
        else:
            print(f"文件大小 > {self.MAX_SINGLE_PART_UPLOAD_SIZE / (1024 * 1024):.0f} MB，执行多部分上传。")
            # 多部分上传后直接调用 attach_uploaded_file，因为这是针对 block 的
            file_upload_result = self._multi_part_upload_content(file_path, file_name, content_type)
        
        if "error" in file_upload_result:
            return file_upload_result
        
        file_upload_id = file_upload_result["id"]
        return self._attach_uploaded_file(file_upload_id, file_name, parent_id, parent_type, content_type)


    def _create_file_upload_object(self, filename: str, content_type: str, mode: str, number_of_parts: int = None):
        """
        在 Notion 中创建文件上传对象。
        """
        create_upload_url = f"{self.base_url}/file_uploads"
        payload = {"mode": mode, "filename": filename, "content_type": content_type}
        if mode == "multi_part" and number_of_parts is not None:
            payload["number_of_parts"] = number_of_parts

        try:
            # 对于这个请求，我们需要确保 Content-Type 是 application/json
            temp_headers = self.headers.copy()
            response = requests.post(create_upload_url, headers=temp_headers, json=payload)
            response.raise_for_status()
            file_upload_data = response.json()
            print(f"已创建文件上传对象，ID: {file_upload_data['id']}")
            return file_upload_data
        except requests.exceptions.RequestException as e:
            print(f"创建文件上传对象时出错: {e}")
            if hasattr(response, 'content'):
                print(f"响应内容: {response.content.decode()}")
            return {"error": str(e), "response_content": response.content.decode() if hasattr(response, 'content') else ""}

    def _single_part_upload_content(self, file_path: str, file_name: str, content_type: str):
        """
        负责上传文件内容（单部分），返回 file_upload 对象的 ID。
        """
        file_upload_data = self._create_file_upload_object(file_name, content_type, "single_part")
        if "error" in file_upload_data:
            return file_upload_data

        file_upload_id = file_upload_data["id"]
        send_url = f"{self.base_url}/file_uploads/{file_upload_id}/send"

        try:
            with open(file_path, "rb") as f:
                # requests 库在使用 `files` 参数时会自动设置 `Content-Type: multipart/form-data` 和边界
                send_headers = self.headers.copy()
                del send_headers["Content-Type"] # 移除可能冲突的 Content-Type

                files = {"file": (file_name, f, content_type)}
                send_response = requests.post(send_url, headers=send_headers, files=files)
                send_response.raise_for_status()
            print(f"文件内容发送成功，文件 ID: {file_upload_id}")
            return {"id": file_upload_id, "name": file_name, "content_type": content_type} # 返回上传成功的ID
        except requests.exceptions.RequestException as e:
            print(f"单部分上传内容时出错: {e}")
            if 'send_response' in locals() and send_response is not None:
                print(f"响应内容: {send_response.content.decode()}")
            return {"error": str(e)}

    def _multi_part_upload_content(self, file_path: str, file_name: str, content_type: str):
        """
        负责上传文件内容（多部分），返回 file_upload 对象的 ID。
        """
        CHUNK_SIZE = 1024 * 1024 * 5  # 5 MB 分块大小
        file_size = os.path.getsize(file_path)
        num_parts = (file_size + CHUNK_SIZE - 1) // CHUNK_SIZE

        file_upload_data = self._create_file_upload_object(file_name, content_type, "multi_part", num_parts)
        if "error" in file_upload_data:
            return file_upload_data

        file_upload_id = file_upload_data["id"]
        send_url = f"{self.base_url}/file_uploads/{file_upload_id}/send"

        try:
            with open(file_path, "rb") as f:
                for i in range(num_parts):
                    f.seek(i * CHUNK_SIZE)
                    chunk = f.read(CHUNK_SIZE)
                    
                    send_headers = self.headers.copy()
                    del send_headers["Content-Type"]

                    files = {
                        "file": (file_name, chunk, content_type),
                        "part_number": (None, str(i + 1)),
                    }
                    
                    send_response = requests.post(send_url, headers=send_headers, files=files)
                    send_response.raise_for_status()
                    print(f"已发送第 {i+1}/{num_parts} 部分，文件 ID: {file_upload_id}")

            complete_url = f"{self.base_url}/file_uploads/{file_upload_id}/complete"
            complete_response = requests.post(complete_url, headers=self.headers, json={})
            complete_response.raise_for_status()
            print(f"已完成多部分上传，文件 ID: {file_upload_id}")
            return {"id": file_upload_id, "name": file_name, "content_type": content_type} # 返回上传成功的ID
        except requests.exceptions.RequestException as e:
            print(f"多部分上传内容时出错: {e}")
            if 'send_response' in locals() and send_response is not None:
                print(f"发送响应内容: {send_response.content.decode()}")
            if 'complete_response' in locals() and complete_response is not None:
                print(f"完成响应内容: {complete_response.content.decode()}")
            return {"error": str(e)}


    def _attach_uploaded_file(self, file_upload_id: str, file_name: str, parent_id: str, parent_type: str, content_type: str):
        """将上传的文件作为新块附加到 Notion 页面或现有块。"""
        create_block_url = f"{self.base_url}/blocks"
        
        if content_type and content_type.startswith("image/"):
            block_type = "image"
        elif content_type and content_type.startswith("video/"):
            block_type = "video"
        elif content_type and content_type.startswith("audio/"):
            block_type = "audio"
        elif content_type and content_type.startswith("application/pdf"):
            block_type = "pdf"
        else:
            block_type = "file"

        block_payload = {
            "children": [
                {
                    "object": "block",
                    "type": block_type,
                    block_type: {
                        "type": "file_upload",
                        "file_upload": {
                            "id": file_upload_id
                        },
                        "caption": [
                            {
                                "type": "text",
                                "text": {
                                    "content": f"{file_name} 通过 API 上传"
                                }
                            }
                        ]
                    }
                }
            ]
        }

        if parent_type == "page_id":
            block_payload["parent"] = {"page_id": parent_id}
        elif parent_type == "block_id":
            create_block_url = f"{create_block_url}/{parent_id}/children"
        else:
            return {"error": "无效的 parent_type。必须是 'page_id' 或 'block_id'。"}

        try:
            headers_for_block_creation = self.headers.copy() # 确保 Content-Type 是 application/json
            response = requests.patch(create_block_url, headers=headers_for_block_creation, json=block_payload) \
                if parent_type == "block_id" else requests.post(create_block_url, headers=headers_for_block_creation, json=block_payload)
            
            response.raise_for_status()
            print(f"文件 '{file_name}' 已成功附加到 {parent_type}: {parent_id}")
            return response.json()
        except requests.exceptions.RequestException as e:
            print(f"将文件附加到 Notion 块时出错: {e}")
            if hasattr(response, 'content'):
                print(f"响应内容: {response.content.decode()}")
            return {"error": str(e), "response_content": response.content.decode() if hasattr(response, 'content') else ""}

    def upload_file_to_database_property(self, file_path: str, page_id: str, property_name: str):
        """
        将文件上传到 Notion 并更新数据库页面的 'file' 属性。

        Args:
            file_path (str): 要上传的文件的路径。
            page_id (str): 数据库页面的 ID，该页面包含要更新的 'file' 属性。
            property_name (str): 数据库中 'file' 属性的名称。

        Returns:
            dict: 更新页面属性的 Notion API 响应或错误消息。
        """
        if not os.path.exists(file_path):
            return {"error": f"文件未找到：{file_path}"}

        file_size = os.path.getsize(file_path)
        file_name = os.path.basename(file_path)
        content_type, _ = mimetypes.guess_type(file_path)
        if content_type is None:
            content_type = "application/octet-stream"

        print(f"准备上传文件：'{file_name}'，以更新数据库属性 '{property_name}'")

        # 1. 上传文件内容到 Notion，获取 file_upload_id
        if file_size <= self.MAX_SINGLE_PART_UPLOAD_SIZE:
            file_upload_result = self._single_part_upload_content(file_path, file_name, content_type)
        else:
            file_upload_result = self._multi_part_upload_content(file_path, file_name, content_type)

        if "error" in file_upload_result:
            return file_upload_result

        file_upload_id = file_upload_result["id"]

        # 2. 更新数据库页面的文件属性
        update_page_url = f"{self.base_url}/pages/{page_id}"
        
        # 构建更新属性的 payload
        # 文件属性的值是一个数组，每个元素是一个文件对象
        # 对于通过 API 上传的文件，使用 "file_upload" 类型和 "id"
        properties_payload = {
            property_name: {
                "type": "files",
                "files": [
                    {
                        "type": "file_upload",
                        "file_upload": {
                            "id": file_upload_id
                        },
                        "name": file_name # 文件属性需要一个 name
                    }
                ]
            }
        }
        
        try:
            # 确保 Content-Type 是 application/json
            response = requests.patch(update_page_url, headers=self.headers, json={"properties": properties_payload})
            response.raise_for_status()
            print(f"数据库页面 '{page_id}' 的属性 '{property_name}' 已成功更新。")
            return response.json()
        except requests.exceptions.RequestException as e:
            print(f"更新数据库页面文件属性时出错: {e}")
            if hasattr(response, 'content'):
                print(f"响应内容: {response.content.decode()}")
            return {"error": str(e), "response_content": response.content.decode() if hasattr(response, 'content') else ""}


# --- 示例用法 ---
if __name__ == "__main__":
   
    
    # 替换为您的 Notion 数据库页面的 ID 和 文件属性的名称
    # 如何获取数据库页面 ID：
    # 1. 打开您的 Notion 数据库。
    # 2. 点击您要更新的某个具体的数据行（页面）。
    # 3. 复制该页面的链接，页面 ID 就是链接中最后一部分的 32 位字符。
    # 例如：https://www.notion.so/myworkspace/My-Database-Entry-1234567890abcdef1234567890abcdef
    # 页面 ID 是 "1234567890abcdef1234567890abcdef"
    
    # 如何获取文件属性名称：
    # 在数据库中，文件属性的列名就是它的名称。
    # 例如，如果您的列名为 "Attachments"，那么 property_name 就是 "Attachments"。
    
    NOTION_DATABASE_PAGE_ID = "YOUR_NOTION_DATABASE_PAGE_ID"  # <--- **替换为您实际的数据库页面 ID**
    DATABASE_FILE_PROPERTY_NAME = "文件" # <--- **替换为您数据库中文件属性的实际名称**

    # 创建一个测试文件
    dummy_file_name = "database_test_file.txt"
    with open(dummy_file_name, "w") as f:
        f.write("This file is uploaded to a Notion database file property.\n")
        f.write("Database integration test.")

    if NOTION_DATABASE_PAGE_ID == "YOUR_NOTION_DATABASE_PAGE_ID" or DATABASE_FILE_PROPERTY_NAME == "文件":
        print("\n请替换 'YOUR_NOTION_DATABASE_PAGE_ID' 和 'DATABASE_FILE_PROPERTY_NAME' 为您的实际值。")
    elif NOTION_TOKEN is None:
        print("\n请设置 NOTION_TOKEN 环境变量。")
    else:
        try:
            uploader = NotionFileUploader(notion_token=NOTION_TOKEN)

            print(f"\n尝试上传 '{dummy_file_name}' 到数据库页面 '{NOTION_DATABASE_PAGE_ID}' 的属性 '{DATABASE_FILE_PROPERTY_NAME}'。")
            result = uploader.upload_file_to_database_property(
                file_path=dummy_file_name,
                page_id=NOTION_DATABASE_PAGE_ID,
                property_name=DATABASE_FILE_PROPERTY_NAME
            )
            print("\n数据库文件属性更新结果:\n", json.dumps(result, indent=2, ensure_ascii=False))

            # 示例：上传一个图片文件到数据库文件属性
            # 如果您有一个图片文件，可以替换下面的路径
            # image_file_name = "my_image.png"
            # if os.path.exists(image_file_name):
            #     print(f"\n尝试上传图片 '{image_file_name}' 到数据库页面 '{NOTION_DATABASE_PAGE_ID}' 的属性 '{DATABASE_FILE_PROPERTY_NAME}'。")
            #     image_result = uploader.upload_file_to_database_property(
            #         file_path=image_file_name,
            #         page_id=NOTION_DATABASE_PAGE_ID,
            #         property_name=DATABASE_FILE_PROPERTY_NAME
            #     )
            #     print("\n图片文件属性更新结果:\n", json.dumps(image_result, indent=2, ensure_ascii=False))


        except ValueError as e:
            print(f"初始化失败: {e}")
        except Exception as e:
            print(f"发生未知错误: {e}")

    # 清理测试文件
    if os.path.exists(dummy_file_name):
        os.remove(dummy_file_name)