import asyncio
import json
import logging
import os
import random
import time
import urllib.parse
from typing import Dict, List, Optional, Any
import os
import sys
# 将父目录添加到 Python 路径
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import execjs
import httpx

from media_platform.douyin.field import SearchChannelType

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler('douyin_search.log', encoding='utf-8')
    ]
)
logger = logging.getLogger('search_user')

# 创建数据目录
os.makedirs("data", exist_ok=True)


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
        
        # 尝试加载JS签名模块
        try:
            logger.info("加载JS签名模块...")
            self.js_code = open('libs/douyin.js', encoding='utf-8-sig').read()
            self.js_executor = execjs.compile(self.js_code)
            logger.info("JS签名模块加载成功")
        except Exception as e:
            logger.error(f"加载JS签名模块失败: {e}", exc_info=True)
            raise
    
    def get_web_id(self) -> str:
        """生成随机的webid"""
        logger.debug("生成随机webid")
        
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
        result = web_id.replace('-', '')[:19]
        logger.debug(f"生成的webid: {result}")
        return result
    
    def get_a_bogus(self, url: str, params: str) -> str:
        """获取a_bogus参数"""
        logger.debug(f"计算a_bogus参数，URL: {url}, 参数长度: {len(params)}")
        try:
            sign_js_name = "sign_datail" if "/reply" not in url else "sign_reply"
            result = self.js_executor.call(sign_js_name, params, self.headers["User-Agent"])
            logger.debug(f"生成的a_bogus参数: {result}")
            return result
        except Exception as e:
            logger.error(f"计算a_bogus参数失败: {e}", exc_info=True)
            raise
    
    async def search_user(self, keyword: str, offset: int = 0, limit: int = 10) -> Dict:
        """搜索用户
        
        Args:
            keyword: 搜索关键词
            offset: 起始偏移量
            limit: 返回结果数量
            
        Returns:
            搜索结果
        """
        logger.info(f"开始搜索用户，关键词: {keyword}, 偏移量: {offset}, 限制: {limit}")
        
        # 构建请求URL
        uri = "/aweme/v1/web/discover/search/"
        url = f"{self._host}{uri}"
        
        # 构建查询参数，参考示例中的参数结构
        query_params = {
            "device_platform": "webapp",
            "aid": "6383",
            "channel": "channel_pc_web",
            "search_channel": SearchChannelType.USER.value,
            "keyword": keyword,
            "search_source": "normal_search",
            "query_correct_type": "1",
            "is_filter_search": "0",
            "from_group_id": "",
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
            "browser_version": "133.0.0.0",
            "browser_online": "true",
            "engine_name": "Blink",
            "engine_version": "133.0.0.0",
            "os_name": "Mac OS",
            "os_version": "10.15.7",
            "cpu_core_num": "10",
            "device_memory": "8",
            "platform": "PC",
            "downlink": "10",
            "effective_type": "4g",
            "round_trip_time": "50",
            "webid": self.get_web_id()
        }
        
        # 从cookie中获取关键值
        for key in ['ttwid', 'msToken', 'odin_tt']:
            if key in self.cookie_dict:
                query_params[key] = self.cookie_dict[key]
                
        # 特殊处理msToken
        if 'msToken' not in query_params and 'msToken' in self.cookie_dict:
            query_params['msToken'] = self.cookie_dict['msToken']
        
        # 更新headers，更接近真实浏览器请求
        headers = self.headers.copy()
        referer_url = f"https://www.douyin.com/search/{urllib.parse.quote(keyword)}?type=user"
        headers["Referer"] = referer_url
        
        # 获取a_bogus参数
        query_string = urllib.parse.urlencode(query_params)
        try:
            a_bogus = self.get_a_bogus(uri, query_string)
            query_params["a_bogus"] = a_bogus
        except Exception as e:
            logger.error(f"获取a_bogus参数失败: {e}")
            # 如果获取a_bogus失败，仍然尝试请求
            
        # 记录请求信息
        logger.debug(f"请求URL: {url}")
        logger.debug(f"请求参数: {json.dumps(query_params, ensure_ascii=False)[:500]}...")
        
        # 发送请求
        try:
            async with httpx.AsyncClient() as client:
                response = await client.get(
                    url, 
                    params=query_params, 
                    headers=headers, 
                    timeout=30
                )
                
                # 检查响应状态
                if response.status_code != 200:
                    logger.error(f"请求失败，状态码: {response.status_code}")
                    logger.debug(f"响应内容: {response.text[:500]}...")
                    return {}
                
                # 解析响应数据
                try:
                    data = response.json()
                    
                    # 检查是否需要重新登录
                    if data.get("status_code") == 8 or "need_login" in str(data):
                        logger.error("响应需要登录，Cookie可能已失效")
                        return {"cookie_invalid": True}
                    
                    # 检查响应是否成功
                    if data.get("status_code") != 0:
                        logger.error(f"响应状态码非0: {data.get('status_code')}, 状态消息: {data.get('status_msg')}")
                        return {}
                    
                    # 检查响应是否包含数据
                    if not data.get("data"):
                        logger.warning(f"响应不包含数据字段")
                        return {"data": []}
                    
                    logger.info(f"请求成功，获取到 {len(data.get('data', []))} 条数据")
                    return data
                    
                except json.JSONDecodeError as e:
                    logger.error(f"解析响应JSON失败: {e}")
                    logger.debug(f"响应内容: {response.text[:500]}...")
                    return {}
                    
        except httpx.RequestError as e:
            logger.error(f"发送请求失败: {e}", exc_info=True)
            return {}
    
    async def get_user_info(self, keyword: str) -> Dict:
        """获取用户信息并保存到文件
        
        Args:
            keyword: 用户关键词
            
        Returns:
            用户信息
        """
        logger.info(f"开始获取用户信息: {keyword}")
        
        # 搜索用户
        search_result = await self.search_user(keyword)
        
        # 检查Cookie是否失效
        if search_result.get("cookie_invalid"):
            logger.error("Cookie已失效，需要刷新")
            return {"cookie_invalid": True}
        
        # 检查是否有搜索结果
        if not search_result or "data" not in search_result:
            logger.warning(f"未找到用户: {keyword}")
            return {}
        
        # 提取用户数据
        user_data = []
        for item in search_result.get("data", []):
            # 用户类型通常为4，但这可能会变化
            if "user_list" in item.get("user_list", {}):
                user_list = item.get("user_list", {}).get("user_list", [])
                user_data.extend(user_list)
        
        if not user_data:
            logger.warning(f"未找到用户数据: {keyword}")
            return {}
        
        # 取第一个用户作为结果
        user = user_data[0]
        logger.info(f"找到用户: {user.get('nickname', 'Unknown')}, uid: {user.get('uid', 'Unknown')}")
        
        # 保存用户数据到文件
        file_path = f"data/{keyword}.json"
        try:
            with open(file_path, "w", encoding="utf-8") as f:
                json.dump(user, f, ensure_ascii=False, indent=4)
            
            logger.info(f"用户数据已保存到: {file_path}")
        except Exception as e:
            logger.error(f"保存用户数据失败: {e}", exc_info=True)
        
        return user
    
    async def save_batch_user_info(self, keywords: List[str], retry_on_invalid_cookie: bool = True) -> Dict[str, Any]:
        """批量获取用户信息
        
        Args:
            keywords: 用户关键词列表
            retry_on_invalid_cookie: 当Cookie无效时是否通知调用者
            
        Returns:
            结果统计
        """
        logger.info(f"开始批量获取用户信息，共 {len(keywords)} 个关键词")
        
        results = {
            "success": 0,
            "fail": 0,
            "cookie_invalid": False,
            "details": {}
        }
        
        for i, keyword in enumerate(keywords):
            logger.info(f"处理第 {i+1}/{len(keywords)} 个关键词: {keyword}")
            
            try:
                # 随机延迟，模拟人类行为
                if i > 0:
                    delay = random.uniform(1, 3)
                    logger.debug(f"随机延迟 {delay:.2f} 秒")
                    await asyncio.sleep(delay)
                
                # 获取用户信息
                result = await self.get_user_info(keyword)
                
                # 检查Cookie是否失效
                if result.get("cookie_invalid"):
                    logger.error("检测到Cookie无效，停止批量获取")
                    results["cookie_invalid"] = True
                    if retry_on_invalid_cookie:
                        return results
                    
                # 记录结果
                if result and not result.get("cookie_invalid"):
                    results["success"] += 1
                    results["details"][keyword] = "success"
                    logger.info(f"成功获取用户 {keyword} 的信息")
                else:
                    results["fail"] += 1
                    results["details"][keyword] = "fail"
                    logger.warning(f"获取用户 {keyword} 的信息失败")
                
            except Exception as e:
                logger.error(f"处理关键词 {keyword} 时出错: {e}", exc_info=True)
                results["fail"] += 1
                results["details"][keyword] = f"error: {str(e)}"
        
        # 输出统计结果
        logger.info(f"批量处理完成，成功: {results['success']}, 失败: {results['fail']}")
        return results