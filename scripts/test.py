import requests
from notion_client import Client
from enum import Enum

class Strategy(Enum):
    IGNORE = 'ignore'
    DELETE = 'delete'
    UPDATE = 'update'

def get_or_create_relation_id(title):
    # 查询数据库以获取关系ID
    relation_id = query_database_for_relation_id(title)
    if relation_id:
        return relation_id
    # 如果关系不存在，则创建它并返回新的ID
    new_relation_id = create_new_relation(title)
    return new_relation_id

def get_property_payload(prop_type, content):
    if prop_type in ['title', 'rich_text']:
        return {
            prop_type: [
                {
                    "text": {
                        "content": content
                    }
                }
            ]
        }
    elif prop_type in ['url', 'number', 'email', 'phone_number', 'checkbox']:
        return {
            prop_type: content
        }
    elif prop_type in ['select', 'status']:
        return {
            prop_type: {
                "name": content
            }
        }
    elif prop_type == 'multi_select':
        return {
            "multi_select": [{"name": name} for name in content]
        }
    elif prop_type == 'date':
        return {
            "date": {
                "start": content
            }
        }
    elif prop_type == 'relation':
        relation_ids = [get_or_create_relation_id(title) for title in content]
        return {
            "relation": [{"id": id} for id in relation_ids]
        }
    # 你可以根据需要添加更多类型的处理
    return None


def fetch_existing_pages(notion, database_id, property_mapping):
    existing_pages = {}
    start_cursor = None

    while True:
        response = notion.databases.query(database_id=database_id, start_cursor=start_cursor)
        for page in response['results']:
            for key, value in property_mapping.items():
                if value in page['properties'] and page['properties'][value]['type'] == 'title':
                    existing_pages[page['properties'][value]['title'][0]['text']['content']] = page['id']

        if not response.get('has_more'):
            break
        start_cursor = response.get('next_cursor')

    return existing_pages

def create_page(notion, database_id, item, property_mapping, properties):
    properties_payload = {}
    for key, value in property_mapping.items():
        if key in item and value in properties:
            prop_type = properties[value]['type']
            properties_payload[value] = get_property_payload(prop_type, item[key])

    notion.pages.create(
        parent={"database_id": database_id},
        properties=properties_payload
    )

def fetch_data_and_insert_to_notion(data_url, notion_token, database_id, property_mapping, strategy=Strategy.IGNORE):
    # 初始化Notion客户端
    notion = Client(auth=notion_token)

    # 发送网络请求获取数据
    response = requests.get(data_url)
    data = response.json()

    # 获取Notion数据库的属性
    database = notion.databases.retrieve(database_id)
    properties = database['properties']

    # 获取Notion数据库中现有的页面
    existing_pages = fetch_existing_pages(notion, database_id, property_mapping)

    # 遍历数据并插入到Notion数据库中
    for item in data:
        item_id = item['id']
        if item_id in existing_pages:
            if strategy == Strategy.IGNORE:
                print(f"ID {item_id} already exists. Skipping.")
                continue
            elif strategy == Strategy.DELETE:
                notion.pages.update(page_id=existing_pages[item_id], archived=True)
                print(f"ID {item_id} already exists. Deleting and re-adding.")
            elif strategy == Strategy.UPDATE:
                properties_payload = {}
                for key, value in property_mapping.items():
                    if key in item and value in properties:
                        prop_type = properties[value]['type']
                        properties_payload[value] = get_property_payload(prop_type, item[key])
                notion.pages.update(page_id=existing_pages[item_id], properties=properties_payload)
                print(f"ID {item_id} already exists. Updating.")
                continue

        # 创建新页面
        create_page(notion, database_id, item, property_mapping, properties)
        if strategy == Strategy.DELETE:
            print(f"ID {item_id} has been re-added.")

    print("数据已成功插入到Notion数据库中")

# 示例调用
data_url = 'https://example.com/api/data'
notion_token = 'your_notion_token'
database_id = 'your_database_id'
property_mapping = {
    "id": "id",
    "title": "标题",
    "cover": "封面"
}
strategy = Strategy.UPDATE  # 可选值: Strategy.IGNORE, Strategy.DELETE, Strategy.UPDATE

fetch_data_and_insert_to_notion(data_url, notion_token, database_id, property_mapping, strategy)