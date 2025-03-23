import asyncio
import argparse
import logging
import time
import json
from typing import List, Dict, Any
import os
import sys
# 将父目录添加到 Python 路径
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from cookie_refresh import CookieRefresher
from search_user import DouyinUserSearcher

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler('douyin_search.log', encoding='utf-8')
    ]
)
logger = logging.getLogger('main')


async def read_users_file(file_path: str) -> List[str]:
    """读取用户列表文件
    
    Args:
        file_path: 用户列表文件路径
        
    Returns:
        用户列表
    """
    logger.info(f"开始读取用户列表文件: {file_path}")
    
    if not os.path.exists(file_path):
        logger.error(f"用户列表文件不存在: {file_path}")
        return []
        
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            users = [line.strip() for line in f.readlines() if line.strip() and not line.strip().startswith("#")]
        
        logger.info(f"成功读取到 {len(users)} 个用户")
        return users
    except Exception as e:
        logger.error(f"读取用户列表文件失败: {e}", exc_info=True)
        return []


async def check_dependencies() -> bool:
    """检查依赖文件是否存在"""
    logger.info("检查必要的依赖文件...")
    
    # 检查libs目录
    if not os.path.exists('libs'):
        logger.error("错误: libs目录不存在，请确保在正确的目录中运行脚本")
        logger.error("请从MediaCrawler项目复制libs目录到当前目录")
        return False
        
    # 检查libs/douyin.js文件
    if not os.path.exists('libs/douyin.js'):
        logger.error("错误: libs/douyin.js文件不存在，请确保正确复制了依赖文件")
        return False
    
    # 检查libs/stealth.min.js文件
    if not os.path.exists('libs/stealth.min.js'):
        logger.error("错误: libs/stealth.min.js文件不存在，请确保正确复制了依赖文件")
        return False
    
    # 检查tools目录
    if not os.path.exists('tools'):
        logger.error("错误: tools目录不存在，请确保在正确的目录中运行脚本")
        logger.error("请从MediaCrawler项目复制tools目录到当前目录")
        return False
        
    # 检查tools/slider_util.py文件
    if not os.path.exists('tools/slider_util.py'):
        logger.error("错误: tools/slider_util.py文件不存在，请确保正确复制了依赖文件")
        return False
        
    # 检查tools/crawler_util.py文件
    if not os.path.exists('tools/crawler_util.py'):
        logger.error("错误: tools/crawler_util.py文件不存在，请确保正确复制了依赖文件")
        return False
    
    # 创建数据目录
    try:
        os.makedirs("data", exist_ok=True)
        logger.info("依赖检查通过，数据目录已确保存在")
        return True
    except Exception as e:
        logger.error(f"创建数据目录失败: {e}")
        return False


async def retry_search_with_refresh(
    users: List[str], 
    headless: bool = True, 
    max_retries: int = 3
) -> Dict[str, Any]:
    """带有Cookie刷新重试机制的搜索
    
    Args:
        users: 用户列表
        headless: 是否使用无头模式
        max_retries: 最大重试次数
        
    Returns:
        搜索结果统计
    """
    logger.info(f"开始搜索流程，用户数: {len(users)}, 无头模式: {headless}, 最大重试次数: {max_retries}")
    
    # 初始化结果统计
    result_stats = {
        "start_time": time.strftime("%Y-%m-%d %H:%M:%S"),
        "total_users": len(users),
        "success": 0,
        "fail": 0,
        "retries": 0
    }
    
    # 初始化Cookie刷新器
    cookie_refresher = CookieRefresher()
    
    # 重试循环
    retry_count = 0
    remaining_users = users.copy()
    
    while retry_count < max_retries and remaining_users:
        # 获取Cookie
        if retry_count == 0:
            logger.info("首次获取Cookie...")
            cookie_str, cookie_dict = await cookie_refresher.get_valid_cookies(headless=headless)
        else:
            logger.warning(f"第 {retry_count} 次刷新Cookie...")
            result_stats["retries"] += 1
            cookie_str, cookie_dict = await cookie_refresher.refresh_cookies(headless=headless)
        
        # 检查Cookie是否获取成功
        if not cookie_str or not cookie_dict:
            logger.error(f"获取Cookie失败，重试次数: {retry_count + 1}/{max_retries}")
            retry_count += 1
            continue
        
        # 初始化搜索器
        searcher = DouyinUserSearcher(cookie_str, cookie_dict)
        
        # 进行批量搜索
        logger.info(f"开始处理剩余 {len(remaining_users)} 个用户")
        batch_results = await searcher.save_batch_user_info(remaining_users)
        
        # 更新统计信息
        result_stats["success"] += batch_results["success"]
        result_stats["fail"] += batch_results["fail"]
        
        # 检查是否需要刷新Cookie
        if batch_results["cookie_invalid"]:
            # 找出已经处理过的用户
            processed_users = []
            for user, status in batch_results["details"].items():
                if status == "success" or status == "fail":
                    processed_users.append(user)
            
            # 更新剩余用户列表
            remaining_users = [user for user in remaining_users if user not in processed_users]
            logger.warning(f"Cookie已失效，还有 {len(remaining_users)} 个用户未处理")
            
            # 增加重试次数
            retry_count += 1
        else:
            # 所有用户处理完毕
            logger.info("所有用户处理完毕")
            remaining_users = []
    
    # 检查是否还有未处理的用户
    if remaining_users:
        logger.error(f"达到最大重试次数，仍有 {len(remaining_users)} 个用户未处理")
        result_stats["fail"] += len(remaining_users)
    
    # 添加结束时间
    result_stats["end_time"] = time.strftime("%Y-%m-%d %H:%M:%S")
    result_stats["elapsed_time"] = time.time() - time.mktime(time.strptime(result_stats["start_time"], "%Y-%m-%d %H:%M:%S"))
    
    # 保存统计结果
    try:
        stats_file = f"data/search_stats_{time.strftime('%Y%m%d_%H%M%S')}.json"
        with open(stats_file, 'w', encoding='utf-8') as f:
            json.dump(result_stats, f, indent=4, ensure_ascii=False)
        logger.info(f"统计结果已保存到: {stats_file}")
    except Exception as e:
        logger.error(f"保存统计结果失败: {e}")
    
    return result_stats


async def main():
    """主函数"""
    parser = argparse.ArgumentParser(description='抖音用户搜索工具')
    parser.add_argument('--users_file', type=str, default='search_user_douyin/users.txt', help='用户列表文件路径')
    parser.add_argument('--headless', action='store_true', help='是否使用无头模式运行浏览器')
    parser.add_argument('--refresh_cookie', action='store_true', help='是否强制刷新Cookie')
    parser.add_argument('--max_retries', type=int, default=3, help='最大重试次数')
    args = parser.parse_args()
    
    # 记录开始时间
    start_time = time.time()
    logger.info("========== 抖音用户搜索工具启动 ==========")
    logger.info(f"参数: users_file={args.users_file}, headless={args.headless}, refresh_cookie={args.refresh_cookie}, max_retries={args.max_retries}")
    
    # 检查依赖
    if not await check_dependencies():
        logger.error("依赖检查失败，程序退出")
        return 1
    
    # 读取用户列表
    users = await read_users_file(args.users_file)
    if not users:
        logger.error(f"用户列表为空，请检查文件: {args.users_file}")
        return 1
    
    logger.info(f"共读取到 {len(users)} 个待搜索用户")
    
    try:
        
        pass
    except Exception as e:
        logger.critical(f"程序执行过程中发生未处理的错误: {e}", exc_info=True)
        return 1
    finally:
        # 确保清理所有资源
        pending = asyncio.all_tasks() - {asyncio.current_task()}
        for task in pending:
            if not task.done():
                task.cancel()
                try:
                    await task
                except asyncio.CancelledError:
                    pass
    
        

if __name__ == "__main__":
    try:
        exit_code = asyncio.run(main())
        sys.exit(exit_code)
    except KeyboardInterrupt:
        logger.info("用户中断程序执行")
        sys.exit(1)
    except Exception as e:
        logger.critical(f"程序执行过程中发生未处理的错误: {e}", exc_info=True)
        sys.exit(1)