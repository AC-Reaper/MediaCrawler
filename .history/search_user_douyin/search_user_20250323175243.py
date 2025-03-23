import asyncio
import json
import os
import random
import time
from typing import Dict, List, Optional

import execjs
import httpx

from media_platform.douyin.field import SearchChannelType


class DouyinUserSearcher:
    """抖音用户搜索类"""
    
    def __init__(self, cookie_str: str, cookie_dict: Dict):
        self.cookie_str = cookie_str
        self.cookie_dict = cookie_dict
        self._host = "https://www.douyin.com"
        self.headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/114.0.0.0 Safari/537.36",
            "Cookie": cookie_str,
            "Host": "www.douyin.com",
            "Origin": "https://www.douyin.com/",
            "Referer": "https://www.douyin.com/",
            "Content-Type": "application/json;charset=UTF-8"
        }
        # 加载JS签名模块
        self.js_code = open('libs/douyin.js', encoding='utf-8-sig').read()
        self.js_executor = execjs.compile(self.js_code)
        
        # 创建数据目录
        os.makedirs("data", exist_ok=True)
    
    def get_web_id(self) -> str:
        """生成随机的webid"""
        def e(t):
            if t is not None:
                return str(t ^ (int(16 * random.random()) >> (t // 4)))
            else:
                return ''.join(
                    [str(int(1e7)), '-', str(int(1e3)), '-', str(int(4e3)), '-', str(int(8e3)), '-', str(int(1e11))]
                )

        web_id = ''.join(
            e(int(x)) if x in '018' else x for x in e(None)
        )
        return web_id.replace('-', '')[:19]
    
    def get_a_bogus(self, url: str, params: str) -> str:
        """获取a_bogus参数"""
        sign_js_name = "sign_datail" if "/reply" not in url else "sign_reply"
        return self.js_executor.call(sign_js_name, params, self.headers["User-Agent"])
    
    # 在 search_user.py 中的 search_user 方法中：

    async def search_user(self, keyword: str, offset: int = 0, limit: int = 10) -> Dict:
        """搜索用户
        
        Args:
            keyword: 搜索关键词
            offset: 起始偏移量
            limit: 返回结果数量
            
        Returns:
            搜索结果
        """
        # 构建请求URL
        url = f"{self._host}/aweme/v1/web/discover/search/"
        
        # 构建查询参数，参考示例中的参数结构
        query_params = {
            "device_platform": "webapp",
            "aid": "6383",
            "channel": "channel_pc_web",
            "search_channel": "aweme_user_web",
            "keyword": keyword,
            "search_source": "normal_search",
            "query_correct_type": "1",
            "is_filter_search": "0",
            "offset": offset,
            "count": limit,
            "pc_client_type": "1",
            "version_code": "170400",
            "version_name": "17.4.0",
            "cookie_enabled": "true",
            "screen_width": "1920",
            "screen_height": "1080",
            "browser_language": "zh-CN",
            "browser_platform": "MacIntel",
            "browser_name": "Chrome",
            "browser_online": "true",
            "engine_name": "Blink",
            "os_name": "Mac OS",
            "platform": "PC",
            "downlink": "10",
            "effective_type": "4g",
            "round_trip_time": "50",
            "webid": self.get_web_id()
        }
        
        # 从cookie_dict中提取可能需要的值
        if "ttwid" in self.cookie_dict:
            query_params["ttwid"] = self.cookie_dict["ttwid"]
        
        # 更新headers，更接近真实浏览器请求
        headers = self.headers.copy()
        headers["referer"] = f"https://www.douyin.com/search/{urllib.parse.quote(keyword)}?type=user"
        
        # 获取a_bogus参数
        from urllib.parse import urlencode
        query_string = urlencode(query_params)
        a_bogus = self.get_a_bogus("/aweme/v1/web/discover/search/", query_string)
        query_params["a_bogus"] = a_bogus
        
        # 发送请求
        async with httpx.AsyncClient() as client:
            response = await client.get(
                url, 
                params=query_params, 
                headers=headers, 
                timeout=30
            )
            
        # 处理响应...
            # 检查响应状态
            if response.status_code != 200:
                print(f"搜索用户失败，状态码: {response.status_code}")
                return {}
            
            # 解析响应数据
            try:
                data = response.json()
                if not data.get("status_code") == 0:
                    print(f"搜索用户失败，错误码: {data.get('status_code')}, 错误信息: {data.get('status_msg')}")
                    return {}
                return data
            except Exception as e:
                print(f"解析响应数据失败: {e}")
                return {}
    
    async def get_user_info(self, keyword: str) -> Dict:
        """获取用户信息并保存到文件
        
        Args:
            keyword: 用户关键词
            
        Returns:
            用户信息
        """
        print(f"正在搜索用户: {keyword}")
        
        # 搜索用户
        search_result = await self.search_user(keyword)
        
        # 检查是否有搜索结果
        if not search_result or not search_result.get("data"):
            print(f"未找到用户: {keyword}")
            return {}
        
        # 提取用户数据
        user_data = []
        for item in search_result.get("data", []):
            if item.get("type") == 4:  # 用户类型
                user_info = item.get("user_list", {}).get("user_list", [])
                user_data.extend(user_info)
        
        if not user_data:
            print(f"未找到用户数据: {keyword}")
            return {}
        
        # 取第一个用户作为结果
        user = user_data[0]
        
        # 保存用户数据到文件
        file_path = f"data/{keyword}.json"
        with open(file_path, "w", encoding="utf-8") as f:
            json.dump(user, f, ensure_ascii=False, indent=4)
        
        print(f"用户数据已保存到: {file_path}")
        return user
    
    async def save_batch_user_info(self, keywords: List[str]) -> None:
        """批量获取用户信息
        
        Args:
            keywords: 用户关键词列表
        """
        for keyword in keywords:
            await self.get_user_info(keyword)
            # 随机延迟1-3秒，避免请求过快
            await asyncio.sleep(random.uniform(1, 3))