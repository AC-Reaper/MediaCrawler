import asyncio
import logging
import os
import time
from typing import Optional, Dict

from playwright.async_api import Page, TimeoutError

from tools.slider_util import Slide, get_tracks

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler('douyin_search.log', encoding='utf-8')
    ]
)
logger = logging.getLogger('captcha')

# 创建验证码截图目录
os.makedirs("captcha_screenshots", exist_ok=True)


async def handle_slider_verification(page: Page, max_attempts: int = 5) -> bool:
    """处理抖音滑块验证码
    
    Args:
        page: Playwright页面对象
        max_attempts: 尝试滑动的最大次数
        
    Returns:
        验证是否成功
    """
    logger.info("检查是否需要进行滑块验证...")
    
    # 先截图记录当前页面状态
    timestamp = int(time.time())
    screenshot_path = f"captcha_screenshots/page_before_check_{timestamp}.png"
    try:
        await page.screenshot(path=screenshot_path)
        logger.debug(f"当前页面截图已保存: {screenshot_path}")
    except Exception as e:
        logger.warning(f"页面截图失败: {e}")
    
    # 检查是否存在滑块验证
    try:
        # 检查是否出现滑块验证码
        back_selector = "#captcha-verify-image"
        logger.debug(f"等待滑块验证码元素: {back_selector}，超时时间: 5秒")
        
        # 等待滑块验证码元素出现
        slider_element = await page.wait_for_selector(
            selector=back_selector, 
            state="visible", 
            timeout=5000
        )
        
        if slider_element:
            logger.info("检测到滑块验证码，准备进行验证...")
            
            # 截图记录验证码状态
            captcha_screenshot = f"captcha_screenshots/captcha_{timestamp}.png"
            await slider_element.screenshot(path=captcha_screenshot)
            logger.debug(f"验证码截图已保存: {captcha_screenshot}")
            
            # 获取页面URL，方便调试
            current_url = page.url
            logger.debug(f"当前页面URL: {current_url}")
        else:
            logger.warning("等待滑块验证码元素返回了，但是元素为空")
            return True
            
    except TimeoutError:
        logger.info("未检测到滑块验证码，继续执行")
        return True
    except Exception as e:
        logger.error(f"检查滑块验证码时出错: {e}", exc_info=True)
        return False
    
    # 处理滑块验证
    attempts = 0
    while attempts < max_attempts:
        try:
            logger.info(f"开始第 {attempts + 1} 次滑块验证尝试...")
            
            # 每次尝试前先截图
            attempt_screenshot = f"captcha_screenshots/attempt_{attempts+1}_{timestamp}.png"
            await page.screenshot(path=attempt_screenshot)
            
            # 执行滑块验证
            success = await verify_slider(page)
            
            if success:
                logger.info(f"🎉 滑块验证成功，共尝试 {attempts + 1} 次")
                
                # 验证成功后截图
                success_screenshot = f"captcha_screenshots/success_{timestamp}.png"
                await page.screenshot(path=success_screenshot)
                
                return True
            
            logger.warning(f"滑块验证失败，重试中... ({attempts + 1}/{max_attempts})")
            attempts += 1
            
            # 点击刷新按钮，重新获取滑块
            try:
                logger.debug("点击刷新按钮获取新的滑块...")
                refresh_button = await page.query_selector(".secsdk_captcha_refresh")
                if refresh_button:
                    await refresh_button.click()
                    await asyncio.sleep(1)
                else:
                    logger.warning("未找到刷新按钮，尝试其他方式刷新验证码")
                    # 尝试刷新页面
                    await page.reload()
                    await page.wait_for_load_state("networkidle")
            except Exception as refresh_error:
                logger.error(f"刷新验证码时出错: {refresh_error}")
                
            # 等待页面稳定
            await asyncio.sleep(2)
            
        except Exception as e:
            logger.error(f"滑块验证过程中出错: {e}", exc_info=True)
            attempts += 1
            
            # 出错后等待一段时间再重试
            await asyncio.sleep(2)
    
    # 记录最终验证失败状态
    logger.error(f"滑块验证失败，已达到最大尝试次数: {max_attempts}")
    fail_screenshot = f"captcha_screenshots/fail_final_{timestamp}.png"
    await page.screenshot(path=fail_screenshot)
    
    return False


async def verify_slider(page: Page) -> bool:
    """执行滑块验证
    
    Args:
        page: Playwright页面对象
        
    Returns:
        验证是否成功
    """
    try:
        # 获取背景图和滑块图
        back_selector = "#captcha-verify-image"
        gap_selector = 'xpath=//*[@id="captcha_container"]/div/div[2]/img[2]'
        
        logger.debug("等待背景图和滑块图加载完成...")
        
        # 等待背景图和滑块图加载完成
        slider_back_element = await page.wait_for_selector(back_selector, timeout=5000)
        gap_element = await page.wait_for_selector(gap_selector, timeout=5000)
        
        if not slider_back_element or not gap_element:
            logger.error("未能获取到背景图或滑块图元素")
            return False
        
        # 获取图片链接
        slider_back_src = await slider_back_element.get_attribute("src")
        gap_src = await gap_element.get_attribute("src")
        
        if not slider_back_src or not gap_src:
            logger.error("无法获取背景图或滑块图的src属性")
            return False
            
        logger.debug(f"背景图URL: {slider_back_src[:50]}...")
        logger.debug(f"滑块图URL: {gap_src[:50]}...")
        
        # 识别滑块位置
        try:
            logger.debug("开始识别滑块位置...")
            slide_app = Slide(gap=gap_src, bg=slider_back_src)
            distance = slide_app.discern()
            
            if not distance or distance <= 0:
                logger.error(f"滑块位置识别失败，返回的距离不正确: {distance}")
                return False
                
            logger.info(f"滑块位置识别成功，距离: {distance}px")
            
        except Exception as e:
            logger.error(f"滑块位置识别过程中出错: {e}", exc_info=True)
            return False
        
        # 获取移动轨迹 - 使用难度更高的easing函数以模拟真实滑动
        try:
            logger.debug("计算滑动轨迹...")
            tracks = get_tracks(distance, level="hard")
            
            if not tracks or len(tracks) == 0:
                logger.error("生成滑动轨迹失败")
                return False
                
            logger.debug(f"生成轨迹点数: {len(tracks)}")
            
            # 优化轨迹，使其更加自然
            if len(tracks) > 0:
                new_last = tracks[-1]
                tracks.pop()
                # 确保总长度准确
                total = sum(tracks)
                if total < distance:
                    new_last += (distance - total)
                elif total > distance:
                    new_last -= (total - distance)
                tracks.append(new_last)
            
        except Exception as e:
            logger.error(f"计算滑动轨迹时出错: {e}", exc_info=True)
            return False
        
        # 获取滑块元素位置
        try:
            logger.debug("获取滑块元素位置...")
            bounding_box = await gap_element.bounding_box()
            if not bounding_box:
                logger.error("无法获取滑块元素位置")
                return False
            
            # 记录滑块坐标
            slider_x = bounding_box["x"]
            slider_y = bounding_box["y"]
            slider_width = bounding_box["width"]
            slider_height = bounding_box["height"]
            logger.debug(f"滑块位置: x={slider_x}, y={slider_y}, w={slider_width}, h={slider_height}")
            
        except Exception as e:
            logger.error(f"获取滑块元素位置时出错: {e}", exc_info=True)
            return False
        
        # 模拟真实的滑动操作
        try:
            logger.info("开始模拟滑动操作...")
            
            # 定位到滑块中心
            start_x = bounding_box["x"] + bounding_box["width"] / 2
            start_y = bounding_box["y"] + bounding_box["height"] / 2
            
            # 移动到滑块位置并按下鼠标
            await page.mouse.move(start_x, start_y)
            await page.mouse.down()
            
            # 添加开始前的停顿，模拟人类思考
            await asyncio.sleep(0.2 + random.random() * 0.3)
            
            # 分阶段移动，模拟人类滑动过程
            current_x = start_x
            for idx, track in enumerate(tracks):
                # 打印部分轨迹点
                if idx % 5 == 0:
                    logger.debug(f"轨迹点 {idx}: {track}px")
                    
                current_x += track
                # 添加随机的垂直移动，更像人类操作
                random_y_offset = (track % 3 - 1) * 0.5
                await page.mouse.move(current_x, start_y + random_y_offset, steps=5)
                # 添加微小延迟
                await asyncio.sleep(0.01)
            
            # 添加结束后的停顿
            await asyncio.sleep(0.1 + random.random() * 0.2)
            await page.mouse.up()
            
            logger.info("滑动操作完成，等待验证结果...")
            
        except Exception as e:
            logger.error(f"执行滑动操作时出错: {e}", exc_info=True)
            return False
        
        # 等待验证结果
        try:
            # 检查验证码元素是否消失，表示验证成功
            await page.wait_for_selector(back_selector, state="hidden", timeout=5000)
            logger.info("验证码元素已消失，验证成功")
            return True
        except TimeoutError:
            # 检查是否有错误提示
            page_content = await page.content()
            if "操作过慢" in page_content:
                logger.warning("滑动验证失败: 操作过慢")
            elif "提示重新操作" in page_content:
                logger.warning("滑动验证失败: 需要重新操作")
            else:
                logger.warning("滑动验证失败: 验证码元素未消失")
            return False
            
    except Exception as e:
        logger.error(f"滑块验证过程发生错误: {e}", exc_info=True)
        return False


# 导入随机模块，放在最后避免循环导入
import random