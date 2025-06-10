import requests
import json

def generate_activation_codes(count):
    """
    调用API生成指定数量的激活码，并按格式输出。

    Args:
        count (int): 需要生成的激活码数量。

    Returns:
        str: 按格式排列的激活码字符串。
             如果API调用失败或返回数据格式不正确，则返回错误信息。
    """
    api_url = "https://api.notionhub.app/generate-code"
    headers = {'Content-Type': 'application/json'}
    activation_codes = []
    error_count = 0

    print(f"正在尝试调用API {count} 次以生成激活码...")

    for i in range(count):
        try:
            response = requests.post(api_url, headers=headers)
            response.raise_for_status() # 如果请求失败 (状态码 4xx 或 5xx), 会抛出 HTTPError 异常

            # 尝试解析 JSON 数据
            try:
                data = response.json()
                if "activationCode" in data:
                    activation_codes.append(data["activationCode"])
                    print(f"成功获取激活码 ({i+1}/{count}): {data['activationCode']}")
                else:
                    print(f"错误 ({i+1}/{count}): API响应中未找到 'activationCode'。响应内容: {response.text}")
                    error_count += 1
            except json.JSONDecodeError:
                print(f"错误 ({i+1}/{count}): API响应不是有效的JSON格式。响应内容: {response.text}")
                error_count += 1

        except requests.exceptions.RequestException as e:
            print(f"错误 ({i+1}/{count}): 调用API时发生网络错误: {e}")
            error_count += 1
        except Exception as e:
            print(f"错误 ({i+1}/{count}): 发生未知错误: {e}")
            error_count += 1

    if error_count > 0:
        print(f"\n在 {count} 次调用中，有 {error_count} 次失败。")

    if activation_codes:
        formatted_codes = "\n".join([f"* {code}" for code in activation_codes])
        return formatted_codes
    elif error_count == count:
        return "所有API调用均失败，未能获取任何激活码。"
    else:
        return "未能成功获取任何激活码，但部分调用可能成功但未返回有效数据。"

# 调用函数生成30个激活码
num_codes_to_generate = 30
result_string = generate_activation_codes(num_codes_to_generate)

print("\n--- 激活码列表 ---")
print(result_string)