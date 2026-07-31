import re
from urllib.parse import urljoin
import requests

def obtain_html(url):
    """
    接收一个 URL，返回该 URL 的网页 HTML 内容，并修复相对路径资源。
    
    参数:
    url (str): 维基百科页面的 URL
    
    返回:
    str: 网页的 HTML 内容，如果失败则返回 None
    """
    try:
        # 发送 HTTP 请求获取网页内容，禁用 SSL 验证
        response = requests.get(url, verify=False)
        
        # 检查请求是否成功
        if response.status_code == 200:
            html_content = response.text
            
            # 修改 HTML 中的相对路径为绝对路径
            base_url = url  # 基础 URL 即输入的 URL，用于生成完整的资源路径
            html_content = update_resource_paths(html_content, base_url)
            
            # 进一步处理内嵌的 CSS 和 JavaScript 文件路径
            html_content = update_inline_styles_and_scripts(html_content, base_url)
            
            return html_content
        else:
            print(f"Error: Unable to fetch the page, status code: {response.status_code}")
            return None
    except requests.RequestException as e:
        print(f"Error fetching the URL: {e}")
        return None

def update_resource_paths(html_content, base_url):
    """
    更新 HTML 内容中的所有相对路径为绝对路径
    
    参数:
    html_content (str): 原始 HTML 内容
    base_url (str): 网页的基础 URL，用于生成完整路径
    
    返回:
    str: 更新后的 HTML 内容
    """
    # 修复 <img> 标签中的图片路径
    html_content = re.sub(r'<img [^>]*src=["\']([^"\']+)["\']', 
                          lambda match: update_url(match, base_url), html_content)
    
    # 修复 <link> 标签中的 CSS 路径
    html_content = re.sub(r'<link [^>]*href=["\']([^"\']+)["\']', 
                          lambda match: update_url(match, base_url), html_content)
    
    # 修复 <script> 标签中的 JS 路径
    html_content = re.sub(r'<script [^>]*src=["\']([^"\']+)["\']', 
                          lambda match: update_url(match, base_url), html_content)
    
    return html_content

def update_inline_styles_and_scripts(html_content, base_url):
    """
    更新 HTML 中的内联 CSS 和 JavaScript 文件路径
    """
    # 如果 HTML 中有内联的 <style> 或 <script>，你可能需要进一步修复其中引用的相对路径
    html_content = re.sub(r'url\(["\']?([^"\']+)["\']?\)', 
                          lambda match: 'url("' + urljoin(base_url, match.group(1)) + '")', html_content)
    return html_content

def update_url(match, base_url):
    """
    将相对路径转换为绝对路径
    
    参数:
    match (re.Match): 匹配的结果
    base_url (str): 基础 URL，用于生成完整的路径
    
    返回:
    str: 更新后的资源 URL
    """
    resource_url = match.group(1)  # 获取资源路径
    # 如果路径是相对路径，使用 urljoin 转换为绝对路径
    if not resource_url.startswith(('http://', 'https://')):
        return match.group(0).replace(resource_url, urljoin(base_url, resource_url))
    return match.group(0)
