# 声明：本代码仅供学习和研究目的使用。使用者应遵守以下原则：
# 1. 不得用于任何商业用途。
# 2. 使用时应遵守目标平台的使用条款和robots.txt规则。
# 3. 不得进行大规模爬取或对平台造成运营干扰。
# 4. 应合理控制请求频率，避免给目标平台带来不必要的负担。
# 5. 不得用于任何非法或不当的用途。
#
# 详细许可条款请参阅项目根目录下的LICENSE文件。
# 使用本代码即表示您同意遵守上述原则和LICENSE中的所有条款。


# 基础配置
PLATFORM = "py"
KEYWORDS = "罗翔说刑法"  # 关键词搜索配置，以英文逗号分隔
LOGIN_TYPE = "cookie"  # qrcode or phone or cookie
COOKIES = """
UIFID_TEMP=9e5c45806baed1121aef2e4ebdb50ae0783a7b9267143d29acaade7dde1bacd5a92c40ab66689dc1f8c68eaf59801d5b847f0e2d1c0333de9ba33ec64a5c90a79f6b51d4e0c73739508a290bdb48c288; fpk1=U2FsdGVkX1/PKtQ3Vq+fcDsIxK0vqzxRGWN0dN02KRs8t5aXLwOCYIDmCy2Azlr1l7dHOyIKAPFmqsXunEvyMQ==; fpk2=fe0673f2a48d047b912b27e2a0c02f9f; UIFID=9e5c45806baed1121aef2e4ebdb50ae0783a7b9267143d29acaade7dde1bacd53742973d210dbff870c4a475597f3141ca31962a84b0d9defca52fca7c5242df39d1959ff007a38d82e550ee27e4e1706caf31675ca6bb0ea3983de0b0352203f958d4641da75cea513c6a4ed33f85442ceeb04ee7f191e1ec822f83b181127bb11d092a527a86657877a9d287401912887c0af057c8b864daee022a1011f65a; ttwid=1%7CVRFDYLWq6BFUpmWO5HGCfv-h8zLlefBjGp6jJbJq5dk%7C1736086850%7C23c39514a01282d580a6cc48961f25821f84f849ce16b154de939e25ba1b832a; hevc_supported=true; xgplayer_user_id=992741850221; bd_ticket_guard_client_web_domain=2; d_ticket=4d16831a5750d7870cd33f86778a606205c89; passport_assist_user=Cjxo5t2Cli5uOuSLOA0gpeTAWLwsQ4SK49N_67vTIgQdA7YoIGMhQ5hQaNwZvt2qs_HwIu2YvOUNr22p99UaSgo8El5U-ncRCQlidznuoLYBbogTkARU572GhV30NX_7pI9SkashUT8Oq6Oo0h0FWBte6hbw4_qe-lox2NjEEOWy5g0Yia_WVCABIgEDoyrjvA%3D%3D; n_mh=evdRNvFICoBHmtRwDC8GOMNpmDA0nvGXqYAou9z6Fz4; login_time=1736444562390; uid_tt=66562259b7d3f4572502b04a6cf467e7; uid_tt_ss=66562259b7d3f4572502b04a6cf467e7; sid_tt=3f4186576fb85929dacce649dc6c7461; sessionid=3f4186576fb85929dacce649dc6c7461; sessionid_ss=3f4186576fb85929dacce649dc6c7461; is_staff_user=false; store-region=cn-gd; store-region-src=uid; live_use_vvc=%22false%22; xgplayer_device_id=88740610379; volume_info=%7B%22isUserMute%22%3Afalse%2C%22isMute%22%3Afalse%2C%22volume%22%3A0.715%7D; SEARCH_RESULT_LIST_TYPE=%22single%22; x-web-secsdk-uid=c7fa0c41-df46-43a3-b2d9-bc7b74be6ae2; csrf_session_id=6362166513a61153afe6b5b3c2685655; SelfTabRedDotControl=%5B%7B%22id%22%3A%227405401366744533001%22%2C%22u%22%3A20%2C%22c%22%3A0%7D%5D; passport_csrf_token=e78f46b56e8c53f6417ea33e806c236f; passport_csrf_token_default=e78f46b56e8c53f6417ea33e806c236f; sid_guard=3f4186576fb85929dacce649dc6c7461%7C1741614579%7C5184000%7CFri%2C+09-May-2025+13%3A49%3A39+GMT; sid_ucp_v1=1.0.0-KDZmMTE3Y2M1Y2QyODA4NzIyZmJmNDNkMDBjOGY2ZWEyZmRmNGVkMTAKGQjEv6ma_AEQ89u7vgYY7zEgDDgGQPQHSAQaAmhsIiAzZjQxODY1NzZmYjg1OTI5ZGFjY2U2NDlkYzZjNzQ2MQ; ssid_ucp_v1=1.0.0-KDZmMTE3Y2M1Y2QyODA4NzIyZmJmNDNkMDBjOGY2ZWEyZmRmNGVkMTAKGQjEv6ma_AEQ89u7vgYY7zEgDDgGQPQHSAQaAmhsIiAzZjQxODY1NzZmYjg1OTI5ZGFjY2U2NDlkYzZjNzQ2MQ; s_v_web_id=verify_m8inqhr6_phz013Sp_M76b_4DfY_AzK3_646bprQ655Sg; douyin.com; xg_device_score=7.666742553508002; device_web_cpu_core=10; device_web_memory_size=8; dy_swidth=1728; dy_sheight=1117; strategyABtestKey=%221742554129.27%22; biz_trace_id=292125e7; __security_mc_1_s_sdk_crypt_sdk=c6d0d9c1-44cd-8916; __security_mc_1_s_sdk_cert_key=5fb9ab77-4a7d-aef8; __security_mc_1_s_sdk_sign_data_key_web_protect=ed090f9e-40d0-8966; publish_badge_show_info=%220%2C0%2C0%2C1742554137565%22; is_dash_user=1; stream_recommend_feed_params=%22%7B%5C%22cookie_enabled%5C%22%3Atrue%2C%5C%22screen_width%5C%22%3A1728%2C%5C%22screen_height%5C%22%3A1117%2C%5C%22browser_online%5C%22%3Atrue%2C%5C%22cpu_core_num%5C%22%3A10%2C%5C%22device_memory%5C%22%3A8%2C%5C%22downlink%5C%22%3A10%2C%5C%22effective_type%5C%22%3A%5C%224g%5C%22%2C%5C%22round_trip_time%5C%22%3A150%7D%22; bd_ticket_guard_client_data=eyJiZC10aWNrZXQtZ3VhcmQtdmVyc2lvbiI6MiwiYmQtdGlja2V0LWd1YXJkLWl0ZXJhdGlvbi12ZXJzaW9uIjoxLCJiZC10aWNrZXQtZ3VhcmQtcmVlLXB1YmxpYy1rZXkiOiJCTGhrK0lBUGR5VDBQRTBVSi9xR0FsRjdnRmRxMStJVnd3SWwxZnVoUnkzK0VZRTNtTWRUWis3T0pQcVlxdUFsbnBiVkJ3T0lVWDlhcmpPdjRzS1VpL289IiwiYmQtdGlja2V0LWd1YXJkLXdlYi12ZXJzaW9uIjoyfQ%3D%3D; FOLLOW_LIVE_POINT_INFO=%22MS4wLjABAAAA91OjW8qa8TJYFqwFLbS0pG1IfxAYU5cV8QdUDqccyA8%2F1742572800000%2F0%2F0%2F1742557240721%22; FOLLOW_NUMBER_YELLOW_POINT_INFO=%22MS4wLjABAAAA91OjW8qa8TJYFqwFLbS0pG1IfxAYU5cV8QdUDqccyA8%2F1742572800000%2F0%2F0%2F1742557840721%22; odin_tt=e20e4e4ba812bb68a9cdf554931265beb4dfa80caf01ae3ad6757dc73d1f51f570078ee750b00f49541c8950bea8b435455e5acfbd668ebf22d981c97379ee7d; WallpaperGuide=%7B%22showTime%22%3A0%2C%22closeTime%22%3A0%2C%22showCount%22%3A0%2C%22cursor1%22%3A22%2C%22cursor2%22%3A6%7D; IsDouyinActive=false; passport_fe_beating_status=false; __ac_nonce=067dedc48004ea7b2a93c; __ac_signature=_02B4Z6wo00f015OeTeQAAIDAwWFt.wM7bP-TvklAAINBdWV0ROW4lzvLcW5rKpdSP7Pug7ESSaP.9L56ZoYmcZIRPkHzrizaJFHdSEmXmfxJbnUd1fMatLP80kb6-w9SfC4Y3NhmIMW-d7KL22; home_can_add_dy_2_desktop=%220%22
"""

# 具体值参见media_platform.xxx.field下的枚举值，暂时只支持小红书
SORT_TYPE = "popularity_descending"
# 具体值参见media_platform.xxx.field下的枚举值，暂时只支持抖音
PUBLISH_TIME_TYPE = 0
CRAWLER_TYPE = (
    "user_search"  # 爬取类型，search(关键词搜索) | detail(帖子详情)| creator(创作者主页数据)
)
# 自定义User Agent（暂时仅对XHS有效）
UA = 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/131.0.0.0 Safari/537.36 Edg/131.0.0.0'

# 是否在搜索到用户后爬取用户的视频
ENABLE_GET_USER_VIDEOS = False

# 每个用户最多爬取的视频数量
USER_MAX_VIDEOS_COUNT = 20

# 是否开启 IP 代理
ENABLE_IP_PROXY = False

# 未启用代理时的最大爬取间隔，单位秒（暂时仅对XHS有效）
CRAWLER_MAX_SLEEP_SEC = 2

# 代理IP池数量
IP_PROXY_POOL_COUNT = 2

# 代理IP提供商名称
IP_PROXY_PROVIDER_NAME = "kuaidaili"

# 设置为True不会打开浏览器（无头浏览器）
# 设置False会打开一个浏览器
# 小红书如果一直扫码登录不通过，打开浏览器手动过一下滑动验证码
# 抖音如果一直提示失败，打开浏览器看下是否扫码登录之后出现了手机号验证，如果出现了手动过一下再试。
HEADLESS = False

# 是否保存登录状态
SAVE_LOGIN_STATE = True

# 数据保存类型选项配置,支持三种类型：csv、db、json, 最好保存到DB，有排重的功能。
SAVE_DATA_OPTION = "json"  # csv or db or json

# 用户浏览器缓存的浏览器文件配置
USER_DATA_DIR = "%s_user_data_dir"  # %s will be replaced by platform name

# 爬取开始页数 默认从第一页开始
START_PAGE = 1

# 爬取视频/帖子的数量控制
CRAWLER_MAX_NOTES_COUNT = 200

# 并发爬虫数量控制
MAX_CONCURRENCY_NUM = 1

# 是否开启爬图片模式, 默认不开启爬图片
ENABLE_GET_IMAGES = False

# 是否开启爬评论模式, 默认开启爬评论
ENABLE_GET_COMMENTS = True

# 爬取一级评论的数量控制(单视频/帖子)
CRAWLER_MAX_COMMENTS_COUNT_SINGLENOTES = 10

# 是否开启爬二级评论模式, 默认不开启爬二级评论
# 老版本项目使用了 db, 则需参考 schema/tables.sql line 287 增加表字段
ENABLE_GET_SUB_COMMENTS = False

# 已废弃⚠️⚠️⚠️指定小红书需要爬虫的笔记ID列表
# 已废弃⚠️⚠️⚠️ 指定笔记ID笔记列表会因为缺少xsec_token和xsec_source参数导致爬取失败
# XHS_SPECIFIED_ID_LIST = [
#     "66fad51c000000001b0224b8",
#     # ........................
# ]

# 指定小红书需要爬虫的笔记URL列表, 目前要携带xsec_token和xsec_source参数
XHS_SPECIFIED_NOTE_URL_LIST = [
    "https://www.xiaohongshu.com/explore/66fad51c000000001b0224b8?xsec_token=AB3rO-QopW5sgrJ41GwN01WCXh6yWPxjSoFI9D5JIMgKw=&xsec_source=pc_search"
    # ........................
]

# 指定抖音需要爬取的ID列表
DY_SPECIFIED_ID_LIST = [
    "7280854932641664319",
    "7202432992642387233",
    # ........................
]

# 指定快手平台需要爬取的ID列表
KS_SPECIFIED_ID_LIST = ["3xf8enb8dbj6uig", "3x6zz972bchmvqe"]

# 指定B站平台需要爬取的视频bvid列表
BILI_SPECIFIED_ID_LIST = [
    "BV1d54y1g7db",
    "BV1Sz4y1U77N",
    "BV14Q4y1n7jz",
    # ........................
]

# 指定微博平台需要爬取的帖子列表
WEIBO_SPECIFIED_ID_LIST = [
    "4982041758140155",
    # ........................
]

# 指定weibo创作者ID列表
WEIBO_CREATOR_ID_LIST = [
    "5533390220",
    # ........................
]

# 指定贴吧需要爬取的帖子列表
TIEBA_SPECIFIED_ID_LIST = []

# 指定贴吧名称列表，爬取该贴吧下的帖子
TIEBA_NAME_LIST = [
    # "盗墓笔记"
]

# 指定贴吧创作者URL列表
TIEBA_CREATOR_URL_LIST = [
    "https://tieba.baidu.com/home/main/?id=tb.1.7f139e2e.6CyEwxu3VJruH_-QqpCi6g&fr=frs",
    # ........................
]

# 指定小红书创作者ID列表
XHS_CREATOR_ID_LIST = [
    "63e36c9a000000002703502b",
    # ........................
]

# 指定Dy创作者ID列表(sec_id)
DY_CREATOR_ID_LIST = [
    "MS4wLjABAAAATJPY7LAlaa5X-c8uNdWkvz0jUGgpw4eeXIwu_8BhvqE",
    # ........................
]

# 指定bili创作者ID列表(sec_id)
BILI_CREATOR_ID_LIST = [
    "20813884",
    # ........................
]

# 指定快手创作者ID列表
KS_CREATOR_ID_LIST = [
    "3x4sm73aye7jq7i",
    # ........................
]


# 指定知乎创作者主页url列表
ZHIHU_CREATOR_URL_LIST = [
    "https://www.zhihu.com/people/yd1234567",
    # ........................
]

# 指定知乎需要爬取的帖子ID列表
ZHIHU_SPECIFIED_ID_LIST = [
    "https://www.zhihu.com/question/826896610/answer/4885821440", # 回答
    "https://zhuanlan.zhihu.com/p/673461588", # 文章
    "https://www.zhihu.com/zvideo/1539542068422144000" # 视频
]

# 词云相关
# 是否开启生成评论词云图
ENABLE_GET_WORDCLOUD = False
# 自定义词语及其分组
# 添加规则：xx:yy 其中xx为自定义添加的词组，yy为将xx该词组分到的组名。
CUSTOM_WORDS = {
    "零几": "年份",  # 将“零几”识别为一个整体
    "高频词": "专业术语",  # 示例自定义词
}

# 停用(禁用)词文件路径
STOP_WORDS_FILE = "./docs/hit_stopwords.txt"

# 中文字体文件路径
FONT_PATH = "./docs/STZHONGS.TTF"

# 爬取开始的天数，仅支持 bilibili 关键字搜索，YYYY-MM-DD 格式，若为 None 则表示不设置时间范围，按照默认关键字最多返回 1000 条视频的结果处理
START_DAY = '2024-01-01'

# 爬取结束的天数，仅支持 bilibili 关键字搜索，YYYY-MM-DD 格式，若为 None 则表示不设置时间范围，按照默认关键字最多返回 1000 条视频的结果处理
END_DAY = '2024-01-01'

# 是否开启按每一天进行爬取的选项，仅支持 bilibili 关键字搜索
# 若为 False，则忽略 START_DAY 与 END_DAY 设置的值
# 若为 True，则按照 START_DAY 至 END_DAY 按照每一天进行筛选，这样能够突破 1000 条视频的限制，最大程度爬取该关键词下的所有视频
ALL_DAY = False