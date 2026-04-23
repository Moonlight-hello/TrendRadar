#!/usr/bin/env python3
"""
测试东方财富API
"""
import requests
import json
import re
import time
import random

stock_code = "301293"
gbapi_url = "https://gbapi.eastmoney.com"

# 生成callback
callback = f"jsonp_{int(time.time() * 1000)}_{random.randint(100, 999)}"

url = f"{gbapi_url}/webarticlelist/api/Article/Articlelist"
params = {
    'code': stock_code,
    'type': 0,
    'ps': 10,
    'p': 1,
    'sort': 1,
    'callback': callback
}

print("请求URL:", url)
print("参数:", params)
print()

try:
    response = requests.get(url, params=params, timeout=30, verify=False)
    print("状态码:", response.status_code)
    print("响应长度:", len(response.text))
    print()
    print("原始响应（前1000字符）:")
    print(response.text[:1000])
    print()

    # 尝试解析JSONP
    text = response.text.strip()

    if text.startswith('jsonp_'):
        start_idx = text.find('(')
        end_idx = text.rfind(')')
        if start_idx != -1 and end_idx != -1:
            json_str = text[start_idx + 1:end_idx]
            data = json.loads(json_str)
            print("解析成功！")
            print("数据键:", list(data.keys()))

            if 're' in data:
                posts = data['re']
                print(f"帖子数量: {len(posts)}")
                if posts:
                    print("\n第一个帖子示例:")
                    print(json.dumps(posts[0], indent=2, ensure_ascii=False))
            else:
                print("完整数据:")
                print(json.dumps(data, indent=2, ensure_ascii=False))
    else:
        print("不是JSONP格式，尝试直接解析JSON")
        data = json.loads(text)
        print("数据:", json.dumps(data, indent=2, ensure_ascii=False))

except Exception as e:
    print("错误:", e)
    import traceback
    traceback.print_exc()
