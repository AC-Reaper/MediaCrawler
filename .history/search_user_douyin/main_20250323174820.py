import asyncio
import argparse
import os
import sys

from cookie_refresh import CookieRefresher
from search_user import DouyinUserSearcher


async def read_users_file(file_path: str):
    """读取用户列表文件
    
    Args:
        file_path: 用户列表文件路径
        
    Returns:
        用户列表
    """
    if not os.path.exists(file_path):
        print(f"用户列表文件不存在: {file_path}")
        return []
        
    with open(file_path, 'r', encoding='utf-8') as f:
        users = [line.strip() for line in f.readlines() if line.strip()]
    
    return users


async def main():
    """主函数"""
    parser = argparse.ArgumentParser(description='抖音用户搜索工具')
    parser.add_argument('--users_file', type=str, default='users.txt', help='用户列表文件路径')
    parser.add_argument('--headless', action='store_true', help='是否使用无头模式运行浏览器')
    parser.add_argument('--refresh_cookie', action='store_true', help='是否强制刷新Cookie')
    args = parser.parse_args()
    
    # 检查libs目录是否存在
    if not os.path.exists('libs'):
        print("错误: libs目录不存在，请确保在正确的目录中运行脚本")
        print("请从MediaCrawler项目复制libs目录到当前目录")
        sys.exit(1)
        
    # 检查libs/douyin.js文件是否存在
    if not os.path.exists('libs/douyin.js'):
        print("错误: libs/douyin.js文件不存在，请确保正确复制了依赖文件")
        sys.exit(1)
    
    # 检查libs/stealth.min.js文件是否存在
    if not os.path.exists('libs/stealth.min.js'):
        print("错误: libs/stealth.min.js文件不存在，请确保正确复制了依赖文件")
        sys.exit(1)
    
    print("开始抖音用户搜索任务...")
    
    # 读取用户列表
    users = await read_users_file(args.users_file)
    if not users:
        print(f"用户列表为空，请检查文件: {args.users_file}")
        sys.exit(1)
    
    print(f"共读取到 {len(users)} 个待搜索用户")
    
    # 初始化Cookie刷新器
    cookie_refresher = CookieRefresher()
    
    # 获取或刷新Cookie
    if args.refresh_cookie:
        print("强制刷新Cookie...")
        cookie_str, cookie_dict = await cookie_refresher.refresh_cookies(headless=args.headless)
    else:
        cookie_str, cookie_dict = await cookie_refresher.get_valid_cookies(headless=args.headless)
    
    if not cookie_str or not cookie_dict:
        print("获取Cookie失败，请检查网络连接或手动操作")
        sys.exit(1)
    
    # 初始化用户搜索器
    searcher = DouyinUserSearcher(cookie_str, cookie_dict)
    
    # 批量搜索用户
    await searcher.save_batch_user_info(users)
    
    print("所有用户搜索任务已完成!")


if __name__ == "__main__":
    asyncio.run(main())