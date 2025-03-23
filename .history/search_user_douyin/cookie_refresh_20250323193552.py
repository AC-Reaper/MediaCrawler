import asyncio
import os
import json
import logging
import time
from typing import Dict, Optional, Tuple
import sys
# 将父目录添加到 Python 路径
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from playwright.async_api import BrowserContext, Page, async_playwright

from captcha import handle_slider_verification
from tools.crawler_util import convert_cookies

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler('douyin_search.log', encoding='utf-8')
    ]
)
logger = logging.getLogger('cookie_refresh')


class CookieRefresher:
    """用于管理和刷新抖音Cookie的类"""
    
    def __init__(self):
        self.index_url = "https://www.douyin.com"
        self.cookie_file = "cookies.json"
        self.context_page = None
        self.browser_context = None
        self._cookie_timestamp = None
        self.browser_initialized = False  # 标记浏览器是否已初始化
        
    async def init_browser(self, headless: bool = False) -> None:
        """初始化浏览器并访问抖音首页"""
        logger.info(f"开始初始化浏览器，headless模式: {headless}")
        try:
            async with async_playwright() as playwright:
                # 启动浏览器
                chromium = playwright.chromium
                self.browser_context = await self.launch_browser(
                    chromium,
                    None,
                    user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/114.0.0.0 Safari/537.36",
                    headless=headless
                )
                
                # 加载stealth.js防止被检测
                await self.browser_context.add_init_script(path="libs/stealth.min.js")
                
                # 创建新页面并访问抖音首页
                self.context_page = await self.browser_context.new_page()
                self.context_page.set_default_timeout(30000)  # 30秒
                
                # 直接访问抖音主站
                logger.info(f"正在访问抖音首页: {self.index_url}")
                response = await self.context_page.goto(self.index_url)
                await self.context_page.wait_for_load_state("networkidle")
                
                # 处理登录弹窗
                await self.close_login_dialog()
                
                # 处理可能出现的滑块验证
                await handle_slider_verification(self.context_page)
                
                # 保存Cookie
                await self.save_cookies()
                
                return self.browser_context, self.context_page
        except Exception as e:
            logger.error(f"初始化浏览器出错: {e}", exc_info=True)
            raise
    
    async def launch_browser(self, chromium, playwright_proxy, user_agent, headless=False):
        """启动浏览器并创建浏览器上下文"""
        logger.info(f"启动浏览器，headless模式: {headless}, user_agent: {user_agent}")
        
        try:
            user_data_dir = os.path.join(os.getcwd(), "browser_data", "douyin_user_data")
            os.makedirs(user_data_dir, exist_ok=True)
            logger.debug(f"浏览器用户数据目录: {user_data_dir}")
            
            browser_context = await chromium.launch_persistent_context(
                user_data_dir=user_data_dir,
                accept_downloads=True,
                headless=headless,
                proxy=playwright_proxy,
                viewport={"width": 1080, "height": 720},
                user_agent=user_agent
            )
            logger.info("浏览器启动成功")
            return browser_context
        except Exception as e:
            logger.error(f"启动浏览器失败: {e}", exc_info=True)
            raise
    
    async def close_login_dialog(self) -> None:
        """检测登录弹窗但不关闭它"""
        logger.info("检测登录弹窗...")
        
        try:
            # 等待登录弹窗出现
            login_dialog = await self.context_page.wait_for_selector(
                "xpath=//div[contains(@class, 'login-guide-container')]", 
                timeout=5000
            )
            
            if login_dialog:
                logger.info("检测到登录弹窗，准备进行登录")
                await login_dialog.screenshot(path="login_dialog.png")
            else:
                logger.info("未检测到登录弹窗")
                
        except Exception as e:
            logger.info(f"检测登录弹窗时出错或未出现登录弹窗: {e}")
    
    async def save_cookies(self) -> None:
        """保存当前浏览器上下文的Cookie到文件"""
        if not self.browser_context:
            logger.error("浏览器上下文未初始化，无法保存Cookie")
            return
            
        try:
            # 获取所有cookie，包括所有域名
            cookies = await self.browser_context.cookies()
            
            # 查找 msToken 相关的 cookie
            ms_token_cookie = next((c for c in cookies if c.get("name") == "msToken"), None)
            if ms_token_cookie:
                logger.info(f"发现 msToken cookie: {ms_token_cookie.get('domain')} - {ms_token_cookie.get('value')[:10]}...")
            
            # 转换格式
            cookie_str, cookie_dict = convert_cookies(cookies)
            
            # 获取本地存储中的 msToken（如果 cookie 中没有）
            if "msToken" not in cookie_dict:
                try:
                    local_storage = await self.context_page.evaluate("() => window.localStorage")
                    if "msToken" in local_storage:
                        cookie_dict["msToken"] = local_storage["msToken"]
                        logger.info(f"从本地存储中获取到 msToken: {local_storage['msToken'][:10]}...")
                except Exception as e:
                    logger.warning(f"获取本地存储中的 msToken 失败: {e}")
            
            # 记录Cookie获取时间
            save_data = {
                "cookie_str": cookie_str,
                "cookie_dict": cookie_dict,
                "timestamp": int(time.time()),
                "save_time": time.strftime("%Y-%m-%d %H:%M:%S", time.localtime())
            }
            
            # 保存到文件
            with open(self.cookie_file, "w", encoding="utf-8") as f:
                json.dump(save_data, f, ensure_ascii=False, indent=4)
            
            logger.info(f"Cookie已成功保存，包含 {len(cookie_dict)} 个键值对")
        except Exception as e:
            logger.error(f"保存Cookie时出错: {e}", exc_info=True)
    
    async def load_cookies(self) -> Tuple[str, Dict]:
        """从文件加载Cookie"""
        logger.info(f"尝试从文件加载Cookie: {self.cookie_file}")
        
        try:
            # 检查文件是否存在
            if not os.path.exists(self.cookie_file):
                logger.warning(f"Cookie文件不存在: {self.cookie_file}")
                return "", {}
                
            # 读取文件内容
            with open(self.cookie_file, "r", encoding="utf-8") as f:
                data = json.load(f)
                
            # 检查数据格式
            if "cookie_str" not in data or "cookie_dict" not in data:
                logger.error("Cookie文件格式不正确，缺少必要字段")
                return "", {}
                
            # 检查Cookie保存时间
            if "timestamp" in data:
                save_time = data["timestamp"]
                current_time = int(time.time())
                elapsed_time = current_time - save_time
                self._cookie_timestamp = save_time
                
                if elapsed_time > 7200:  # 2小时
                    logger.warning(f"Cookie可能已过期，保存时间: {data.get('save_time', '未知')}, 已过去: {elapsed_time//60} 分钟")
                else:
                    logger.info(f"Cookie保存时间: {data.get('save_time', '未知')}, 已过去: {elapsed_time//60} 分钟")
            
            # 获取Cookie字符串和字典
            cookie_str = data["cookie_str"]
            cookie_dict = data["cookie_dict"]
            
            # 检查Cookie完整性
            important_keys = ['passport_csrf_token', 'ttwid', 'msToken']
            missing_keys = [key for key in important_keys if key not in cookie_dict]
            
            if missing_keys:
                logger.warning(f"Cookie中缺少重要字段: {', '.join(missing_keys)}")
            
            logger.info(f"成功加载Cookie，包含 {len(cookie_dict)} 个键值对")
            return cookie_str, cookie_dict
            
        except json.JSONDecodeError as e:
            logger.error(f"解析Cookie文件失败: {e}")
            # 备份损坏的文件
            if os.path.exists(self.cookie_file):
                backup_file = f"{self.cookie_file}.bak.{int(time.time())}"
                os.rename(self.cookie_file, backup_file)
                logger.info(f"已将损坏的Cookie文件备份为: {backup_file}")
            return "", {}
            
        except Exception as e:
            logger.error(f"加载Cookie文件时出错: {e}", exc_info=True)
            return "", {}
    
    async def is_cookie_valid(self, cookie_dict: Dict) -> bool:
        """检查Cookie是否有效"""
        logger.info("检查Cookie是否有效...")
        
        # 检查Cookie是否为空
        if not cookie_dict:
            logger.warning("Cookie为空")
            return False
            
        # 检查必要字段
        required_fields = ["passport_csrf_token", "ttwid"]
        for field in required_fields:
            if field not in cookie_dict:
                logger.warning(f"Cookie缺少必要字段: {field}")
                return False
        
        # 检查Cookie保存时间（如果之前保存了timestamps）
        if hasattr(self, "_cookie_timestamp") and self._cookie_timestamp:
            current_time = int(time.time())
            elapsed_time = current_time - self._cookie_timestamp
            if elapsed_time > 86400:  # 24小时
                logger.warning(f"Cookie已存在超过24小时，可能已过期: {elapsed_time//3600}小时")
            
        # 发送测试请求验证Cookie有效性
        logger.info("发送测试请求验证Cookie有效性...")
        try:
            # 创建简单的请求客户端
            import httpx
            
            # 构建请求头
            headers = {
                "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/114.0.0.0 Safari/537.36",
                "Cookie": "; ".join([f"{k}={v}" for k, v in cookie_dict.items()]),
                "Referer": "https://www.douyin.com/"
            }
            
            # 发送请求检查用户信息或其他不需要登录的API
            async with httpx.AsyncClient() as client:
                response = await client.get(
                    "https://www.douyin.com/aweme/v1/web/im/user/info/",
                    headers=headers,
                    timeout=10
                )
                
                # 检查响应
                if response.status_code != 200:
                    logger.warning(f"验证Cookie的请求返回非200状态码: {response.status_code}")
                    return False
                
                # 解析响应数据
                try:
                    data = response.json()
                    if data.get("status_code") == 8 or "need_login" in str(data):
                        logger.warning("API返回需要登录的状态码，Cookie无效")
                        return False
                    
                    logger.info("API请求成功，Cookie有效")
                    return True
                    
                except Exception as e:
                    logger.error(f"解析API响应失败: {e}")
                    logger.debug(f"响应内容: {response.text[:500]}...")
                    return False
                    
        except Exception as e:
            logger.error(f"验证Cookie有效性时出错: {e}", exc_info=True)
            return False
    
    async def refresh_cookies(self, headless: bool = False) -> Tuple[str, Dict]:
    """刷新Cookie但不关闭浏览器"""
    logger.info("开始刷新Cookie流程...")
    
    try:
        if self.browser_initialized and self.context_page:
            # 浏览器已初始化，直接刷新抖音主页
            logger.info("刷新抖音主页...")
            await self.context_page.goto(self.index_url)
            await self.context_page.wait_for_load_state("networkidle")
            
            # 处理可能出现的滑块验证
            await handle_slider_verification(self.context_page)
        else:
            # 浏览器未初始化，需要初始化
            await self.init_browser(headless=headless)
            self.browser_initialized = True
        
        # 保存Cookie
        await self.save_cookies()
        
        # 加载保存的Cookie
        cookie_str, cookie_dict = await self.load_cookies()
        
        return cookie_str, cookie_dict
        
    except Exception as e:
        logger.error(f"刷新Cookie过程中出错: {e}", exc_info=True)
        return "", {}
    
    async def get_valid_cookies(self, headless: bool = False) -> Tuple[str, Dict]:
        """获取有效的Cookie，如果当前Cookie无效则刷新"""
        logger.info("开始获取有效Cookie...")
        
        # 如果浏览器未初始化，则先初始化浏览器
        if not self.browser_initialized:
            logger.info("浏览器未初始化，先进行初始化...")
            await self.init_browser(headless=headless)
            
            # 等待用户登录（最多120秒）
            login_success = False
            max_wait_time = 120  # 秒
            check_interval = 3   # 每3秒检查一次
            
            for _ in range(max_wait_time // check_interval):
                # 检查登录状态
                try:
                    login_panel = await self.context_page.query_selector("#douyin_login_comp_flat_panel")
                    has_login = await self.context_page.evaluate("() => window.localStorage.getItem('HasUserLogin') === '1'")
                    
                    if not login_panel or has_login:
                        logger.info("用户已登录成功")
                        login_success = True
                        break
                        
                except Exception as e:
                    logger.debug(f"检查登录状态时出错: {e}")
                    
                logger.info(f"等待用户登录中... 剩余 {max_wait_time - (_ * check_interval)} 秒")
                await asyncio.sleep(check_interval)
            
            if not login_success:
                logger.warning("等待超时，用户未完成登录")
                return "", {}
            
            # 处理可能出现的滑块验证
            await handle_slider_verification(self.context_page)
            
            # 保存Cookie
            await self.save_cookies()
            self.browser_initialized = True
        
        # 从文件加载Cookie
        cookie_str, cookie_dict = await self.load_cookies()
        
        # 检查Cookie是否有效
        if await self.is_cookie_valid(cookie_dict):
            logger.info("当前Cookie有效，直接使用")
            return cookie_str, cookie_dict
        
        # Cookie无效，刷新页面并重新获取
        return await self.refresh_cookies(headless=headless)
    
    # 修改close方法，使其成为可选操作
    async def close(self, force: bool = False) -> None:
        """关闭浏览器上下文，force=True时强制关闭"""
        if force and self.browser_context:
            try:
                await self.browser_context.close()
                self.browser_initialized = False
                logger.info("浏览器上下文已强制关闭")
            except Exception as e:
                logger.error(f"关闭浏览器上下文时出错: {e}")
        elif not force:
            logger.info("保持浏览器会话活跃，未关闭浏览器")