import re
import json

def extract_json(text):
    match = re.search(r'\{.*\}', text, re.DOTALL)  # 只提取 {} 之间的 JSON
    if match:
        return json.loads(match.group())  # 解析 JSON
    else:
        return None

