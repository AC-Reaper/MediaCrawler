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
        
    async def init_browser(self, headless: bool = False) -> None:
        """初始化浏览器并访问抖音首页"""
        logger.info(f"开始初始化浏览器，headless模式: {headless}")
        try:
            async with async_playwright() as playwright:
                # 启动浏览器
                logger.info("启动Chromium浏览器...")
                chromium = playwright.chromium
                self.browser_context = await self.launch_browser(
                    chromium,
                    None,
                    user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/114.0.0.0 Safari/537.36",
                    headless=headless
                )
                
                # 加载stealth.js防止被检测
                logger.info("加载stealth.js脚本防止爬虫检测...")
                await self.browser_context.add_init_script(path="libs/stealth.min.js")
                
                # 创建新页面并访问抖音首页
                logger.info("创建新页面并访问抖音首页...")
                self.context_page = await self.browser_context.new_page()
                
                # 设置页面超时时间
                self.context_page.set_default_timeout(3000000)  # 30秒
                
                # 监听页面请求
                self.context_page.on("request", lambda request: logger.debug(f"页面请求: {request.method} {request.url}"))
                self.context_page.on("response", lambda response: logger.debug(f"页面响应: {response.status} {response.url}"))
                
                # 访问抖音首页
                logger.info(f"正在访问抖音首页: {self.index_url}")
                response = await self.context_page.goto(self.index_url)
                
                if not response.ok:
                    logger.error(f"访问抖音首页失败，状态码: {response.status}")
                    logger.debug(f"响应内容: {await response.text()}")
                else:
                    logger.info(f"成功访问抖音首页，状态码: {response.status}")
                
                # 等待页面加载完成
                await self.context_page.wait_for_load_state("networkidle")
                logger.info("页面加载完成")
                
                # 处理登录弹窗
                await self.close_login_dialog()
                
                # 处理可能出现的滑块验证
                logger.info("检查是否需要进行滑块验证...")
                await handle_slider_verification(self.context_page)
                
                # 保存Cookie
                logger.info("保存浏览器Cookie...")
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
        """关闭登录弹窗"""
        logger.info("尝试关闭可能出现的登录弹窗...")
        
        try:
            # 等待登录弹窗出现
            logger.debug("等待登录弹窗出现，超时时间: 5秒")
            login_dialog = await self.context_page.wait_for_selector(
                "xpath=//div[contains(@class, 'login-guide-container')]", 
                timeout=5000
            )
            
            if not login_dialog:
                logger.info("未检测到登录弹窗")
                return
                
            logger.info("检测到登录弹窗，尝试关闭")
            
            # 截图记录弹窗状态
            await login_dialog.screenshot(path="login_dialog.png")
            logger.debug("已保存登录弹窗截图: login_dialog.png")
            
            # 找到关闭按钮并点击
            logger.debug("查找关闭按钮...")
            close_button = await login_dialog.query_selector("xpath=//div[contains(@class, 'login-guide-close')]")
            
            if close_button:
                logger.info("找到关闭按钮，点击关闭")
                await close_button.click()
                
                # 等待弹窗消失
                try:
                    logger.debug("等待登录弹窗消失...")
                    await self.context_page.wait_for_selector(
                        "xpath=//div[contains(@class, 'login-guide-container')]", 
                        state="hidden",
                        timeout=3000
                    )
                    logger.info("登录弹窗已成功关闭")
                except Exception as e:
                    logger.warning(f"等待登录弹窗消失出错，可能弹窗未完全关闭: {e}")
            else:
                logger.warning("未找到登录弹窗关闭按钮")
                
                # 尝试点击弹窗外部区域关闭
                logger.debug("尝试点击页面空白区域关闭弹窗")
                await self.context_page.mouse.click(10, 10)
                
        except Exception as e:
            logger.info(f"处理登录弹窗时出错或未出现登录弹窗: {e}")
            
            # 尝试使用JavaScript关闭弹窗
            try:
                logger.debug("尝试使用JavaScript关闭登录弹窗")
                await self.context_page.evaluate("""
                    () => {
                        const closeButtons = document.querySelectorAll('.login-guide-close');
                        if (closeButtons.length > 0) {
                            closeButtons[0].click();
                            return true;
                        }
                        return false;
                    }
                """)
            except Exception as js_error:
                logger.debug(f"JavaScript关闭弹窗失败: {js_error}")
    
    async def save_cookies(self) -> None:
        """保存当前浏览器上下文的Cookie到文件"""
        if not self.browser_context:
            logger.error("浏览器上下文未初始化，无法保存Cookie")
            return
            
        try:
            # 获取所有cookie
            logger.info("获取当前浏览器上下文的所有Cookie...")
            cookies = await self.browser_context.cookies()
            logger.debug(f"获取到 {len(cookies)} 个Cookie")
            
            # 转换格式
            cookie_str, cookie_dict = convert_cookies(cookies)
            
            # 检查关键Cookie是否存在
            important_keys = ['passport_csrf_token', 'ttwid', 'msToken', 'odin_tt']
            missing_keys = [key for key in important_keys if key not in cookie_dict]
            
            if missing_keys:
                logger.warning(f"以下重要的Cookie未获取到: {', '.join(missing_keys)}")
            else:
                logger.info("已获取所有重要的Cookie")
            
            # 记录Cookie获取时间
            save_data = {
                "cookie_str": cookie_str,
                "cookie_dict": cookie_dict,
                "timestamp": int(time.time()),
                "save_time": time.strftime("%Y-%m-%d %H:%M:%S", time.localtime())
            }
            
            # 保存到文件
            logger.info(f"正在保存Cookie到文件: {self.cookie_file}")
            with open(self.cookie_file, "w", encoding="utf-8") as f:
                json.dump(save_data, f, ensure_ascii=False, indent=4)
            
            logger.info(f"Cookie已成功保存，包含 {len(cookie_dict)} 个键值对")
            
            # 输出一些重要的cookie信息，方便调试
            for key in important_keys:
                if key in cookie_dict:
                    # 只显示部分值，保护隐私
                    value = cookie_dict[key]
                    masked_value = value[:4] + "*" * (len(value) - 8) + value[-4:] if len(value) > 8 else "****"
                    logger.debug(f"Cookie {key}: {masked_value}")
                
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
        """刷新Cookie"""
        logger.info("开始刷新Cookie流程...")
        
        # 删除旧的Cookie文件(可选)
        if os.path.exists(self.cookie_file):
            backup_file = f"{self.cookie_file}.old.{int(time.time())}"
            logger.debug(f"备份旧的Cookie文件到: {backup_file}")
            os.rename(self.cookie_file, backup_file)
        
        try:
            # 初始化浏览器获取新Cookie
            logger.info(f"启动浏览器(headless={headless})获取新Cookie...")
            start_time = time.time()
            await self.init_browser(headless=headless)
            
            # 计算耗时
            elapsed_time = time.time() - start_time
            logger.info(f"浏览器操作完成，耗时: {elapsed_time:.2f}秒")
            
            # 加载保存的Cookie
            logger.info("加载刚刚保存的Cookie...")
            cookie_str, cookie_dict = await self.load_cookies()
            
            # 检查Cookie是否有效
            if not cookie_dict:
                logger.error("刷新Cookie失败，获取的Cookie为空")
                raise Exception("刷新Cookie失败，获取的Cookie为空")
                
            # 检查关键Cookie字段
            important_keys = ['passport_csrf_token', 'ttwid', 'msToken']
            missing_keys = [key for key in important_keys if key not in cookie_dict]
            
            if missing_keys:
                logger.warning(f"刷新后的Cookie缺少重要字段: {', '.join(missing_keys)}")
            
            # 记录刷新时间
            self._cookie_timestamp = int(time.time())
            
            logger.info(f"Cookie刷新成功，获取到 {len(cookie_dict)} 个Cookie")
            return cookie_str, cookie_dict
            
        except Exception as e:
            logger.error(f"刷新Cookie过程中出错: {e}", exc_info=True)
            return "", {}
            
        finally:
            # 关闭浏览器
            logger.info("关闭浏览器...")
            await self.close()
    
    async def get_valid_cookies(self, headless: bool = False) -> Tuple[str, Dict]:
        """获取有效的Cookie，如果当前Cookie无效则刷新"""
        logger.info("开始获取有效Cookie...")
        
        # 先从文件加载Cookie
        cookie_str, cookie_dict = await self.load_cookies()
        
        # 检查是否需要刷新Cookie
        if await self.is_cookie_valid(cookie_dict):
            logger.info("当前Cookie有效，直接使用")
            return cookie_str, cookie_dict
        
        # Cookie无效，需要刷新
        logger.warning("当前Cookie无效，需要刷新")
        return await self.refresh_cookies(headless=headless)
    
    async def close(self) -> None:
        """关闭浏览器上下文"""
        if self.browser_context:
            try:
                await self.browser_context.close()
                logger.info("浏览器上下文已关闭")
            except Exception as e:
                logger.error(f"关闭浏览器上下文时出错: {e}")