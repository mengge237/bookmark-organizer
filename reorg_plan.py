#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
收藏夹全量重组方案生成器 v2
- 用「文件夹链列表 + 书签名」分离模型，避免书签名含 / 的歧义
- 按管理学 MECE 原则重建 9 大分类
- 输出: 收藏夹重组方案.md (审核用) + reorg_plan.json (执行用)
"""
import json

SRC = r"C:\Users\Lenovo\AppData\Local\Microsoft\Edge\User Data\Default\Bookmarks"
OUT_MD = r"E:\NET Program\bookmark-organizer\收藏夹重组方案.md"
OUT_JSON = r"E:\NET Program\bookmark-organizer\reorg_plan.json"

# 规则: (路径特征, URL特征或None, 目标路径, 改名或None)
# 目标路径以 "/" 结尾 = 子树搬迁（保留内部子结构）
RULES = [
    # ===== 原「开发工具」子树 =====
    ("开发工具/skill", None, "AI 工具/Skill与MCP/", None),
    ("开发工具/材质和hdr", None, "建模美术/材质与HDR/", None),
    ("开发工具/贴图", None, "建模美术/贴图/", None),
    ("开发工具/模型", None, "建模美术/模型与动画/", None),
    ("开发工具/动画", None, "建模美术/模型与动画/", None),
    ("开发工具/参考", "pinterest.com", "建模美术/参考与图库", "Pinterest"),
    ("开发工具/参考/新标签页", "pixiv.net", "建模美术/参考与图库", "Pixiv"),
    ("开发工具/参考", "artstation.com", "建模美术/参考与图库", "ArtStation"),
    ("开发工具/参考/GGAC", None, "建模美术/参考与图库", None),
    ("开发工具/参考/www.deviantart.com", None, "建模美术/参考与图库", None),
    ("开发工具/图片资源", None, "建模美术/参考与图库/", None),
    ("中国科学技术大学测速网站", None, "系统网络/在线工具", None),
    ("news.ycombinator.com", None, "开发工具/社区资讯", None),
    ("IT eBooks", None, "开发工具/编程学习", None),
    ("Newest Questions - Stack Overflow", None, "开发工具/社区资讯", None),
    ("云风的 BLOG", None, "开发工具/社区资讯", None),

    # ===== 原「常用工具」 =====
    ("DeepSeek | 深度求索", None, "AI 工具/对话助手", None),
    ("工作台 - Gitee.com", None, "开发工具/代码托管", None),
    ("腾讯混元3D", None, "AI 工具/生图与模型", None),
    ("常用工具/GitHub", None, "开发工具/代码托管", None),
    ("常用工具/Yandex", None, "娱乐/图片资源", None),
    ("Git Stars", None, "开发工具/代码托管", None),
    ("学习通", None, "学习考试/课程平台", None),
    ("常用工具/Poly Haven", None, "回收站", None),
    ("物联网平台_设备接入", None, "开发工具/物联网硬件", None),
    ("文心一言", None, "AI 工具/对话助手", None),
    ("Docker Home", None, "系统网络/系统与运维", None),
    ("扣子编程", None, "AI 工具/开发平台", None),
    ("扣子 - AI办公助手", None, "AI 工具/开发平台", None),
    ("V2Fun", None, "AI 工具/开发平台", None),
    ("搜索AI伙伴", None, "AI 工具/对话助手", None),
    ("GitHub上整理的一些工具", None, "开发工具/编程学习", None),
    ("哔哩哔哩 (゜-゜)", None, "娱乐/影音平台", None),

    # ===== 原「工具」 =====
    ("尚德机构个人中心", None, "学习考试/课程平台", None),
    ("视频库", None, "学习考试/课程平台", None),
    ("中国大学MOOC", None, "学习考试/课程平台", None),
    ("英语（一）.pdf", None, "学习考试/英语", None),
    ("Blockade Labs", None, "AI 工具/生图与模型", None),
    ("在线转换文档", None, "系统网络/在线工具", None),
    ("AI R18 Generator", None, "娱乐/资源/游戏与模组", None),
    ("IP地址查询", None, "系统网络/在线工具", None),
    ("在线抠图软件", None, "AI 工具/生图与模型", None),
    ("AI万能助手地址", None, "AI 工具/对话助手", None),
    (None, "e-hentai.org", "娱乐/资源/漫画本子", None),
    ("歌曲宝", None, "娱乐/音乐", None),
    ("HTML颜色代码表", None, "前端与设计/配色", None),
    ("配色表", None, "前端与设计/配色", None),
    ("色板", None, "前端与设计/配色", None),
    ("HTML 表格", None, "前端与设计/前端教程", None),
    ("Worldvectorlogo", None, "前端与设计/图标与logo", None),
    ("logotyp", None, "前端与设计/图标与logo", None),
    ("阿里巴巴矢量图标库", None, "前端与设计/图标与logo", None),
    ("Boxicons", None, "前端与设计/图标与logo", None),
    ("HTML5 Canvas", None, "前端与设计/前端教程", None),
    ("JavaScript 创建一个下拉菜单", None, "前端与设计/前端教程", None),
    ("响应式导航栏", None, "前端与设计/前端教程", None),
    ("HTML 游戏障碍物", None, "前端与设计/前端教程", None),
    ("背景色之颜色渐变", None, "前端与设计/前端教程", None),
    ("扫雷小游戏制作教程", None, "前端与设计/前端教程", None),
    ("Staticfile CDN", None, "前端与设计/前端教程", None),
    ("花猫导航官网 — Yandex", None, "回收站", None),
    ("Ionicons", None, "前端与设计/图标与logo", None),
    ("Clippy", None, "前端与设计/前端教程", None),
    ("font-awesome - Libraries - cdnjs", None, "前端与设计/图标与logo", None),
    ("Font Awesome", None, "前端与设计/图标与logo", None),
    ("菜鸟教程", None, "开发工具/编程学习", None),
    ("稀土掘金", None, "开发工具/社区资讯", None),
    ("w3cschool", None, "开发工具/编程学习", None),
    ("w3school 在线教程", None, "开发工具/编程学习", None),
    ("编程工具/CSDN", None, "开发工具/社区资讯", None),
    ("GitHub 中文社区", None, "开发工具/代码托管", None),
    ("Git · GitHub", None, "开发工具/代码托管", None),
    ("MDN Web Docs", None, "开发工具/编程学习", None),
    ("Java 全栈知识体系", None, "开发工具/编程学习", None),
    ("CS-Notes", None, "开发工具/编程学习", None),
    ("Road 2 Coding", None, "开发工具/编程学习", None),
    ("豆丁素材网", None, "建模美术/素材与音效", None),
    ("办公资源网", None, "建模美术/素材与音效", None),
    ("菜鸟图库", None, "建模美术/素材与音效", None),
    ("tileable", None, "建模美术/材质与HDR", None),
    ("Blender模型下载", None, "建模美术/材质与HDR", None),
    ("PBR Materials", None, "建模美术/材质与HDR", None),
    ("ImgOnline", None, "系统网络/在线工具", None),
    ("Transparent Textures", None, "建模美术/材质与HDR", None),
    ("Free Stock Textures", None, "建模美术/材质与HDR", None),
    ("建模工具/材质/花猫导航", None, "系统网络/导航与资讯", None),
    ("BEIZ", None, "建模美术/游戏美术资源", None),
    ("爱给网", None, "建模美术/素材与音效", None),
    ("耳聆网", None, "建模美术/素材与音效", None),
    ("从模型制作（3dmax）到网页显示", None, "建模美术/建模教程", None),
    ("魔酷网", None, "建模美术/游戏美术资源", None),
    ("Three.js实战", None, "建模美术/建模教程", None),
    ("ImageToStl", None, "建模美术/建模教程", None),
    ("创造家社区", None, "建模美术/游戏美术资源", None),
    ("Three.js Basic template", None, "建模美术/建模教程", None),
    ("GameBanana", None, "游戏/Mod与资源", None),
    ("辉辉的Mod库", None, "游戏/Mod与资源", None),
    ("建模工具/Mixamo", None, "回收站", None),
    ("MMD Tools", None, "建模美术/建模教程", None),
    ("glTF Viewer", None, "建模美术/建模教程", None),
    ("1000 Logos", None, "前端与设计/图标与logo", None),
    ("老梦C4D", None, "建模美术/建模教程", None),
    ("quaternius", None, "建模美术/游戏美术资源", None),
    ("synty", None, "建模美术/游戏美术资源", None),
    ("Home · Kenney", None, "建模美术/游戏美术资源", None),
    ("OpenGameArt", None, "建模美术/游戏美术资源", None),
    ("CGTrader", None, "建模美术/游戏美术资源", None),
    ("工具/VPN/PrivadoVPN", None, "系统网络/VPN", None),
    ("VPN工具", None, "系统网络/VPN", None),
    ("工具/VPN/PrivadoVPN Plans", None, "回收站", None),
    ("2925邮箱", None, "系统网络/账号与认证", None),
    ("DFRobot官网", None, "开发工具/物联网硬件", None),
    ("物联网平台SDK下载地址", None, "开发工具/物联网硬件", None),
    ("iot.dfrobot", None, "开发工具/物联网硬件", None),
    ("Sunny-Ngrok", None, "系统网络/内网穿透", None),
    ("Summary - Overview", None, "开发工具/代码托管", None),
    ("立创开源硬件平台", None, "开发工具/物联网硬件", None),
    ("小智 AI 聊天机器人", None, "开发工具/物联网硬件", None),
    ("3dsinghvfx", None, "建模美术/游戏美术资源", None),
    ("Pixso", None, "前端与设计/设计工具", None),
    ("advanced-java", None, "开发工具/编程学习", None),
    ("DeepSeek 开放平台", None, "AI 工具/开发平台", None),
    ("国家数据集管理服务系统", None, "开发工具/数据与API", None),
    ("xxyun - 导航", None, "系统网络/导航与资讯", None),
    ("星辰VPN", None, "系统网络/VPN", None),
    ("网站推荐 - 哔哩哔哩", None, "娱乐/影音平台", None),

    # ===== 原「实战」 =====
    ("中国计算机技术职业资格网", None, "学习考试/考试报名", None),
    ("全国计算机技术与软件专业技术资格", None, "学习考试/考试报名", None),
    ("中国人事考试网", None, "学习考试/考试报名", None),
    ("四、六级考试报名网", None, "学习考试/考试报名", None),
    ("计算机等级考试考务管理系统", None, "学习考试/考试报名", None),
    ("数学建模竞赛", None, "学习考试/备考与刷题", None),
    ("LoginView", None, "学习考试/备考与刷题", None),
    ("软考通", None, "回收站", None),
    ("普通话水平测试", None, "学习考试/考试报名", None),
    ("蓝桥杯", None, "学习考试/考试报名", None),
    ("Poliigon", None, "建模美术/材质与HDR", None),
    ("力扣", None, "开发工具/刷题与竞赛", None),
    ("实战/PTA", None, "开发工具/刷题与竞赛", None),
    ("实战/上网认证", None, "系统网络/账号与认证", None),
    ("2508.19484", None, "学习考试/论文科研", None),
    ("ComfyUI Examples", None, "AI 工具/生图与模型", None),
    ("实战/github.com", None, "开发工具/代码托管", None),
    ("Deployment Paused", None, "AI 工具/生图与模型", None),
    ("HF-Mirror", None, "AI 工具/生图与模型", None),
    ("吐司 tusi.cn", None, "AI 工具/生图与模型", None),
    ("LiblibAI", None, "AI 工具/生图与模型", None),
    ("天聚数行", None, "开发工具/数据与API", None),
    ("认证", None, "学习考试/考试报名", None),

    # ===== 原「娱乐」 =====
    ("风车动漫", None, "娱乐/影音平台", None),
    ("Anime Scene Search", None, "娱乐/图片资源", None),
    ("Yandex Images", None, "娱乐/图片资源", None),
    ("漫画阅读Manga", None, "娱乐/漫画资源", None),
    ("漫自由", None, "娱乐/漫画资源", None),
    ("Jiumo Search", None, "娱乐/小说资源", None),
    ("Taco搜索", None, "娱乐/小说资源", None),
    ("GOG.com", None, "游戏/账号与交易", None),
    # ===== 娱乐/资源 细分（62 条按内容类型 6 类） =====
    (None, "hanime1.me", "娱乐/资源/动画里番", None),
    (None, "hanime4u.com", "娱乐/资源/动画里番", None),
    (None, "h-ani.com", "娱乐/资源/动画里番", None),
    (None, "hianime.to", "娱乐/资源/动画里番", None),
    (None, "gg-animes.com", "娱乐/资源/动画里番", None),
    (None, "yuepxpau", "娱乐/资源/动画里番", None),
    (None, "manga18.me", "娱乐/资源/漫画本子", None),
    (None, "5mantt.com", "娱乐/资源/漫画本子", None),
    (None, "theteenxxx.pro", "娱乐/资源/漫画本子", None),
    (None, "xprem.icu", "娱乐/资源/漫画本子", None),
    (None, "18-comicfreedom", "娱乐/资源/漫画本子", None),
    (None, "jmcomic1.ltd", "娱乐/资源/漫画本子", None),
    (None, "jm18c", "娱乐/资源/漫画本子", None),
    (None, "smallcolor.link", "娱乐/资源/漫画本子", None),
    (None, "ukdevilz.com", "娱乐/资源/视频", None),
    (None, "iwara.tv", "娱乐/资源/视频", None),
    (None, "rule34video.com", "娱乐/资源/视频", None),
    (None, "sugaranime.com", "娱乐/资源/游戏与模组", None),
    (None, "aqxaromods.com", "娱乐/资源/游戏与模组", None),
    (None, "lookatvintage.com/best", "娱乐/资源/游戏与模组", None),
    (None, "itch.io", "娱乐/资源/游戏与模组", None),
    (None, "acgyx.us", "娱乐/资源/游戏与模组", None),
    (None, "dlsite.com", "娱乐/资源/游戏与模组", None),
    (None, "r34nsfw.com", "娱乐/资源/图片Coser", None),
    (None, "mitaku.net", "娱乐/资源/图片Coser", None),
    (None, "anyscroll.com", "娱乐/资源/图片Coser", None),
    (None, "/highlights", "娱乐/资源/图片Coser", None),
    (None, "joyreactor.com", "娱乐/资源/图片Coser", None),
    (None, "tgsearch.org", "娱乐/资源/社区与搜索", None),
    (None, "gollum.space", "娱乐/资源/社区与搜索", None),
    (None, "x.com/home", "娱乐/资源/社区与搜索", None),
    (None, "vpn-china.org", "回收站", None),
    (None, "livejasmin.com", "回收站", None),
    (None, "cursor-free-vip", "AI 工具/开发平台", None),
    (None, "craftpix.net", "建模美术/游戏美术资源", None),
    ("娱乐/PrivadoVPN", None, "系统网络/VPN", None),
    ("Awesome-BongoCat", None, "开发工具/Unity开发", None),
    ("Unity3D制作桌宠核心代码", None, "开发工具/Unity开发", None),
    ("无忧梦呓", None, "游戏/Mod与资源", None),
    (None, "cz01.org", "回收站", None),
    (None, "https://czzyv.com/", "娱乐/影音平台", None),
    ("AGE动漫", None, "娱乐/影音平台", None),

    # ===== 原「教程」 =====
    ("Unity的窗口透明化", None, "开发工具/Unity开发", None),
    ("简单的桌宠（米塔）", None, "开发工具/Unity开发", None),
    ("PlasticSCM", None, "开发工具/Unity开发", None),
    ("Unity：从入门到入行", None, "开发工具/Unity开发", None),
    ("原神桌宠", None, "开发工具/Unity开发", None),
    ("validation failed", None, "开发工具/Unity开发", None),
    ("error CS0006", None, "开发工具/Unity开发", None),
    ("EndLayoutGroup", None, "开发工具/Unity开发", None),
    ("another Unity instance", None, "开发工具/Unity开发", None),
    ("PMX模型转FBX模型", None, "建模美术/建模教程", None),
    ("DOTween", None, "开发工具/Unity开发", None),
    ("BongoCat 支持导入自定义模型", None, "开发工具/Unity开发", None),
    ("AI桌面精灵/宠物", None, "开发工具/Unity开发", None),
    ("Windows桌面宠物", None, "开发工具/Unity开发", None),
    ("Unity超简单打包成exe", None, "开发工具/Unity开发", None),
    ("blender案例相关资源", None, "建模美术/建模教程", None),
    ("MMD动作富有生机", None, "建模美术/建模教程", None),
    ("Index of /release/", None, "建模美术/建模教程", None),
    ("Blender学习方法与技巧", None, "建模美术/建模教程", None),
    ("cats-blender-plugin", None, "建模美术/建模教程", None),
    ("MMD零基础入门", None, "建模美术/建模教程", None),
    ("Bootstrap", None, "前端与设计/前端教程", None),
    ("Visual Studio2022发布web", None, "前端与设计/前端教程", None),
    ("做个懂代码的设计师", None, "前端与设计/前端教程", None),
    ("片单卡片设计", None, "前端与设计/前端教程", None),
    ("视差滚动效果", None, "前端与设计/前端教程", None),
    ("昼夜模式动画", None, "前端与设计/前端教程", None),
    ("动漫胶囊海报动画", None, "前端与设计/前端教程", None),
    ("Element - 网站快速成型工具", None, "前端与设计/前端教程", None),
    ("wangEditor", None, "前端与设计/前端教程", None),
    ("制作并且维护你的mod", None, "游戏/Mod与资源", None),
    ("mc模组制作入门指南", None, "游戏/Mod与资源", None),
    ("虚幻4游戏解包", None, "游戏/Mod与资源", None),
    ("VMware虚拟机安装Linux", None, "系统网络/系统与运维", None),
    ("windows server 2003", None, "系统网络/系统与运维", None),
    ("Win系统2025版本下载", None, "系统网络/系统与运维", None),
    ("清华大学开源软件镜像站", None, "系统网络/系统与运维", None),
    ("AliParaformerAsr", None, "AI 工具/本地模型与文档", None),
    ("AIGAZOU", None, "AI 工具/生图与模型", None),
    ("Kimi", None, "AI 工具/对话助手", None),
    ("octocode-mcp", None, "AI 工具/Skill与MCP", None),
    ("unity-mcp", None, "AI 工具/Skill与MCP", None),
    ("动手学 Ollama", None, "AI 工具/本地模型与文档", None),
    ("Releases · ollama", None, "AI 工具/本地模型与文档", None),
    ("DeepWiki", None, "AI 工具/本地模型与文档", None),
    ("unity mcp接入", None, "AI 工具/Skill与MCP", None),
    ("BiliNote", None, "学习考试/课程平台", None),
    ("2410.02829", None, "学习考试/论文科研", None),
    ("多视频摘要框架", None, "学习考试/论文科研", None),
    ("Burp Suite", None, "系统网络/抓包与安全", None),
    ("Fiddler入门", None, "系统网络/抓包与安全", None),
    ("9个免费小众音乐下载网站", None, "娱乐/音乐", None),
    ("GitHub检索技巧", None, "开发工具/编程学习", None),
    ("夸克网盘解析", None, "系统网络/在线工具", None),
    ("解析密码获取三步骤", None, "系统网络/在线工具", None),
    ("Navicat 15", None, "系统网络/系统与运维", None),
    ("Manga漫研网", None, "娱乐/漫画资源", None),
    ("SHiFT", None, "游戏/账号与交易", None),
    ("Artistic Asset", None, "建模美术/游戏美术资源", None),
    ("学生学习页面", None, "学习考试/课程平台", None),
    ("杀戮尖塔统计分析", None, "游戏/游戏工具", None),
    ("影音资料的制作和获取", None, "游戏/游戏工具", None),
    ("Documentation | Graphviz", None, "开发工具/编程学习", None),
    (None, "jform2.baidu.com", "回收站", None),

    # ===== 原「游戏工具」 =====
    ("Warframe Market", None, "游戏/游戏工具", None),
    ("MC百科", None, "游戏/Mod与资源", None),
    ("SteamPY", None, "游戏/账号与交易", None),
    ("刷图规划器", None, "游戏/游戏工具", None),
    ("明日方舟工具箱", None, "游戏/游戏工具", None),
    ("排班表生成器", None, "游戏/游戏工具", None),
    ("PRTS Plus", None, "游戏/游戏工具", None),
    ("森空岛", None, "游戏/游戏工具", None),
    ("终末地", None, "游戏/游戏工具", None),
    ("鹰角网络通行证", None, "游戏/账号与交易", None),
    ("游戏工具/明日方舟", None, "游戏/游戏工具", None),
    ("WARFRAME中文维基", None, "游戏/游戏工具", None),
    ("以撒的结合中文维基", None, "游戏/游戏工具", None),

    # ===== 原「其他收藏夹」 =====
    ("DLsite", None, "娱乐/资源/游戏与模组", None),
    ("OpenWeatherMap", None, "开发工具/数据与API", None),
    ("Unity ID", None, "开发工具/Unity开发", None),
    ("C盘哪些文件能删", None, "系统网络/系统与运维", None),
    ("萌娘百科", None, "娱乐/图片资源", None),
    ("JetBrains Account", None, "开发工具", None),
    ("other/上网认证", None, "回收站", None),
    ("SakuraFrp", None, "系统网络/内网穿透", None),
    ("Unity 资源商店", None, "开发工具/Unity开发", None),
    (None, "czzyv.com/movie", "娱乐/影音平台", None),
]

# ===== 开发者推荐网站自动规则（数据源: recommend_sites.py 的 RECOMMEND 目录） =====
# recommend 模式添加的站点在重新生成 plan 时也能被正确归类。
# URL 特征用 "=" 前缀 = 整条 URL 精确匹配（大小写/尾斜杠不敏感）——
# 从构造上杜绝误伤：不会命中同域下的其它页面（如用户的 NSFW 游戏页含 "itch.io"
# 但不会等于 "https://itch.io"），也不会命中 "glitch.io" 这类子串巧合。
try:
    from recommend_sites import RECOMMEND as _RECOMMEND
    for _r in _RECOMMEND:
        RULES.append((None, "=" + _r["url"], "/".join(_r["folders"]), None))
except ImportError:
    pass


def load_bookmarks(src=SRC):
    with open(src, encoding="utf-8") as f:
        d = json.load(f)
    out = []
    for rn, r in d["roots"].items():
        def walk(children, folders):
            for c in children:
                name = c.get("name") or ""
                if c.get("type") == "folder":
                    walk(c.get("children", []), folders + [name])
                else:
                    out.append({"folders": folders, "name": name,
                                "url": c.get("url", ""),
                                "old": "/".join(folders + [name])})
        walk(r.get("children", []), [rn])
    return out


def _norm_url(u):
    return (u or "").strip().rstrip("/").lower()


def match(b):
    # hits 元素: (key, url_key, target, rename, ip)；ip=True 表示"原地匹配"——
    # 路径特征规则（key 含 "/"）是针对整理前结构写的，整理后 key 不再命中；
    # 若书签已位于该规则的目标文件夹，视为等价的原地命中（保证 plan 幂等），
    # 并保留原 key 参与特异性排序——长路径规则仍能压过宽泛的名字子串规则
    # （如 "认证" 命中 "上网认证"，"实战/上网认证" 必须赢）。
    hits = []
    cur = b["folders"][1:]
    for key, url_key, target, rename in RULES:
        k_ok = key is None or key in b["old"]
        ip = False
        if not k_ok and key is not None and "/" in key:
            # 老路径失效 → 原地等价匹配（URL 特征仍需满足，防误改名）
            if url_key is not None:
                if url_key.startswith("="):
                    u_ok = _norm_url(b["url"]) == _norm_url(url_key[1:])
                else:
                    u_ok = url_key in b["url"]
                if not u_ok:
                    continue
            tparts = [s for s in target.split("/") if s]
            if not tparts:
                continue
            if target.endswith("/"):
                k_ok = cur[:len(tparts)] == tparts  # 子树规则：目标链前缀即可
            else:
                k_ok = cur == tparts  # 普通规则：必须精确位于目标文件夹
            ip = k_ok
        if not k_ok:
            continue
        if url_key is None:
            u_ok = True
        elif url_key.startswith("="):  # 精确 URL（推荐目录自动规则专用）
            u_ok = _norm_url(b["url"]) == _norm_url(url_key[1:])
        else:
            u_ok = url_key in b["url"]
        if u_ok:
            hits.append((key, url_key, target, rename, ip))
    if not hits:
        return None
    if len(hits) > 1:
        # 先比路径特征长度，再比 URL 特征长度——更具体的规则优先
        hits.sort(key=lambda h: (-(len(h[0]) if h[0] else 0),
                                 -(len(h[1]) if h[1] else 0)))
        best = (len(hits[0][0]) if hits[0][0] else 0,
                len(hits[0][1]) if hits[0][1] else 0)
        ties = [h for h in hits
                if (len(h[0]) if h[0] else 0, len(h[1]) if h[1] else 0) == best]
        # 目标路径语义比较：子树规则目标带 "/" 后缀，与普通规则指向同一文件夹
        if len({t[2].rstrip("/") for t in ties}) > 1:
            return ("CONFLICT", hits)
    key, url_key, target, rename, ip = hits[0]
    if ip:
        return cur, rename  # 原地命中：位置不变，只应用改名
    if target.endswith("/"):  # 子树搬迁：key 是文件夹链前缀
        key_folders = [s for s in key.split("/") if s]
        # 文件夹链不含根(root)，根恒定且不参与匹配
        fchain = b["folders"][1:]
        if fchain[:len(key_folders)] != key_folders:
            return ("CONFLICT", [("前缀不匹配", target, rename)])
        new_folders = [s for s in target.split("/") if s] + fchain[len(key_folders):]
        return new_folders, rename
    new_folders = [s for s in target.split("/") if s]
    return new_folders, rename


def main(src=SRC, out_md=OUT_MD, out_json=OUT_JSON):
    bookmarks = load_bookmarks(src)
    plan, unmatched, conflicts = [], [], []
    for b in bookmarks:
        m = match(b)
        if m is None:
            unmatched.append(b)
        elif isinstance(m, tuple) and m[0] == "CONFLICT":
            conflicts.append((b, m[1]))
        else:
            new_folders, rename = m
            plan.append({"folders": new_folders, "name": b["name"],
                         "url": b["url"], "old": b["old"], "rename": rename})

    print(f"书签总数: {len(bookmarks)}")
    print(f"已规划: {len(plan)}  未匹配: {len(unmatched)}  冲突: {len(conflicts)}")
    if unmatched:
        print("\n=== 未匹配书签 ===")
        for b in unmatched:
            print(f"  {b['old']}\n    {b['url'][:80]}")
    if conflicts:
        print("\n=== 规则冲突 ===")
        for b, hits in conflicts:
            print(f"  {b['old']}")
            for h in hits:
                print(f"    -> {h}")

    # 目标分布
    counts = {}
    for p in plan:
        key = "/".join(p["folders"]) + ("/" + p["name"] if p["folders"] and False else "")
        counts[p["folders"][0]] = counts.get(p["folders"][0], 0) + 1
    print("\n=== 目标分布 ===")
    for t, n in sorted(counts.items(), key=lambda x: -x[1]):
        print(f"  {t}: {n}")

    # 全部分布（含子文件夹）
    sub_counts = {}
    for p in plan:
        k = "/".join(p["folders"])
        sub_counts[k] = sub_counts.get(k, 0) + 1
    print("\n=== 子文件夹分布 ===")
    for k, n in sorted(sub_counts.items()):
        print(f"  {k}: {n}")

    with open(out_json, "w", encoding="utf-8") as f:
        json.dump(plan, f, ensure_ascii=False, indent=1)

    # Markdown
    tree = {}
    for p in plan:
        node = tree
        for seg in p["folders"]:
            nxt = node.setdefault(seg, {})
            if isinstance(nxt, list):
                nxt = {"_散落": nxt}
                node[seg] = nxt
            node = nxt
        if isinstance(node, dict):
            node.setdefault("_散落", []).append(p)
        else:
            node.append(p)

    lines = ["# 收藏夹全量重组方案（审核稿）\n",
             "> 管理学原则：MECE 互斥穷尽、顶层按领域统一维度、管理幅度 ≤7、层级 ≤3。",
             "> 「回收站」为待清理项（重复/失效），确认后可手动删除。\n"]
    def render(node, depth):
        if isinstance(node, list):
            for b in node:
                rename = f"（改名: {b['rename']}）" if b["rename"] else ""
                name = (b["name"] or "(空名)")[:60]
                url = b["url"][:70]
                lines.append(f"{'  '*depth}- {name} {rename}  `{url}`")
            return
        if "_散落" in node:
            render(node["_散落"], depth)
        for k in sorted(node.keys()):
            if k == "_散落":
                continue
            if isinstance(node[k], dict):
                lines.append(f"\n{'#'*(depth+2)} {k}")
                render(node[k], depth + 1)
            else:
                render(node[k], depth)
    render(tree, 0)
    lines.append("\n## 回收站说明\n")
    notes = {
        "polyhaven.com/zh": "与 建模美术/材质与HDR 中的 Poly Haven 重复",
        "online.yandex.com": "失效搜索页（花猫导航官网残留）",
        "mixamo.com/#/": "与 建模美术/模型与动画 中的 Mixamo 重复",
        "signup.prvd.info": "带 token 的失效升级页",
        "try-learning.com/#/LoginView": "与 学习考试/备考与刷题 中的软考通登录页重复",
        "try-learning.com/#/": "与 学习考试/备考与刷题 中的软考通重复",
        "cz01.org": "旧域名，保留 czzyv.com 那条",
        "jform2.baidu.com": "百度跳转链接，内容不明",
        "eportal": "与 系统网络/账号与认证 重复（校园网认证）",
        "vpn-china.org": "跳转壳链接（书签名只有 F），内容不明",
        "livejasmin.com": "广告带参残留链接（由 lookatvintage 跳转而来）",
    }
    for b in plan:
        if b["folders"] == ["回收站"]:
            for frag, why in notes.items():
                if frag in b["url"]:
                    lines.append(f"- `{b['url'][:70]}` — {why}")
                    break
            else:
                lines.append(f"- `{b['url'][:70]}` — 待定")
    with open(out_md, "w", encoding="utf-8") as f:
        f.write("\n".join(lines))
    print(f"\n方案已写入: {out_md}")
    return bookmarks, plan, unmatched, conflicts


if __name__ == "__main__":
    main()
