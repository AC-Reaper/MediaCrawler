import asyncio
import os
import json
from typing import Dict, Optional, Tuple

from playwright.async_api import BrowserContext, Page, async_playwright

from captcha import handle_slider_verification
from tools.crawler_util import convert_cookies


class CookieRefresher:
    """用于管理和刷新抖音Cookie的类"""
    
    def __init__(self):
        self.index_url = "https://www.douyin.com"
        self.cookie_file = "cookies.json"
        self.context_page = None
        self.browser_context = None
        
    async def init_browser(self, headless: bool = False) -> None:
        """初始化浏览器并访问抖音首页"""
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
            self.context_page = await self.browser_context.new_page()
            await self.context_page.goto(self.index_url)
            
            # 处理登录弹窗
            await self.close_login_dialog()
            
            # 处理可能出现的滑块验证
            await handle_slider_verification(self.context_page)
            
            # 保存Cookie
            await self.save_cookies()
            
            return self.browser_context, self.context_page
    
    async def launch_browser(self, chromium, playwright_proxy, user_agent, headless=False):
        """启动浏览器并创建浏览器上下文"""
        user_data_dir = os.path.join(os.getcwd(), "browser_data", "douyin_user_data")
        os.makedirs(user_data_dir, exist_ok=True)
        
        browser_context = await chromium.launch_persistent_context(
            user_data_dir=user_data_dir,
            accept_downloads=True,
            headless=headless,
            proxy=playwright_proxy,
            viewport={"width": 1920, "height": 1080},
            user_agent=user_agent
        )
        return browser_context
    
    async def close_login_dialog(self) -> None:
        """关闭登录弹窗"""
        try:
            # 等待登录弹窗出现
            login_dialog = await self.context_page.wait_for_selector(
                "xpath=//div[contains(@class, 'login-guide-container')]", 
                timeout=5000
            )
            
            # 找到关闭按钮并点击
            close_button = await login_dialog.query_selector("xpath=//div[contains(@class, 'login-guide-close')]")
            if close_button:
                await close_button.click()
                print("已关闭登录弹窗")
            else:
                print("未找到登录弹窗关闭按钮")
        except Exception as e:
            print(f"处理登录弹窗时出错或未出现登录弹窗: {e}")
    
    async def save_cookies(self) -> None:
        """保存当前浏览器上下文的Cookie到文件"""
        if not self.browser_context:
            print("浏览器上下文未初始化，无法保存Cookie")
            return
            
        cookies = await self.browser_context.cookies()
        cookie_str, cookie_dict = convert_cookies(cookies)
        
        with open(self.cookie_file, "w", encoding="utf-8") as f:
            json.dump({
                "cookie_str": cookie_str,
                "cookie_dict": cookie_dict
            }, f, ensure_ascii=False, indent=4)
        
        print(f"Cookie已保存到文件: {self.cookie_file}")
    
    async def load_cookies(self) -> Tuple[str, Dict]:
        """从文件加载Cookie"""
        try:
            with open(self.cookie_file, "r", encoding="utf-8") as f:
                data = json.load(f)
                return data["cookie_str"], data["cookie_dict"]
        except (FileNotFoundError, json.JSONDecodeError) as e:
            print(f"加载Cookie文件失败: {e}")
            return "", {}
    
    async def is_cookie_valid(self, cookie_dict: Dict) -> bool:
        """检查Cookie是否有效"""
        # 简单判断Cookie是否包含必要字段
        if not cookie_dict or not cookie_dict.get("passport_csrf_token"):
            return False
            
        # 实际应用中可以发送一个测试请求验证Cookie是否有效
        return True
    
    async def refresh_cookies(self, headless: bool = False) -> Tuple[str, Dict]:
        """刷新Cookie"""
        print("正在刷新Cookie...")
        await self.init_browser(headless=headless)
        cookie_str, cookie_dict = await self.load_cookies()
        await self.close()
        return cookie_str, cookie_dict
    
    async def get_valid_cookies(self, headless: bool = False) -> Tuple[str, Dict]:
        """获取有效的Cookie，如果当前Cookie无效则刷新"""
        cookie_str, cookie_dict = await self.load_cookies()
        
        if await self.is_cookie_valid(cookie_dict):
            print("当前Cookie有效，直接使用")
            return cookie_str, cookie_dict
        
        print("当前Cookie无效，需要刷新")
        return await self.refresh_cookies(headless=headless)
    
    async def close(self) -> None:
        """关闭浏览器上下文"""
        if self.browser_context:
            await self.browser_context.close()
            print("浏览器上下文已关闭")