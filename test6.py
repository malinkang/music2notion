from notion_client import Client

# 初始化Notion客户端
notion = Client(auth="secret_xvMkQzLkCRtZL478L8MhvLdIDOxicjjSUm9U9voAwbb")
# 数据库ID
database_id = "f852878351c7450db17f85b68410ce44"

# 获取当前数据库属性
database = notion.databases.retrieve(database_id=database_id)

# 要删除的属性名称
property_to_remove = "平台"

# 移除属性
# if property_to_remove in properties:
#     del properties[property_to_remove]
properties = {
    "平台":None
}
# 更新数据库
notion.databases.update(
    database_id=database_id,
    properties=properties
)