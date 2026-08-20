# -*- coding: utf-8 -*-
"""开发者推荐网站目录（recommend 命令的数据源）。

每个条目: name / url / folders(收藏夹目标路径, ≤3 级) / why(推荐理由)。
选装后走 push 管道（官方 API）进入收藏夹并同步到云端；
reorg_plan.py 会自动为每个条目生成归类规则，保证后续 plan 仍能正确识别。
"""
import json

RECOMMEND = [
    # ===== 开发工具/效率工具（新子文件夹） =====
    {"name": "DevDocs", "url": "https://devdocs.io", "folders": ["开发工具", "效率工具"],
     "why": "几十种语言/框架的 API 文档聚合，一个站点离线速查"},
    {"name": "regex101", "url": "https://regex101.com", "folders": ["开发工具", "效率工具"],
     "why": "正则在线调试：实时解释 + 多语言语法 + 单元测试"},
    {"name": "IT-Tools", "url": "https://it-tools.tech", "folders": ["开发工具", "效率工具"],
     "why": "开发者常用在线工具箱合集（编码/转换/时间戳/哈希/UUID…）"},
    {"name": "JSON Crack", "url": "https://jsoncrack.com", "folders": ["开发工具", "效率工具"],
     "why": "JSON 转可视化图形，复杂结构一眼看懂"},
    {"name": "Transform", "url": "https://transform.tools", "folders": ["开发工具", "效率工具"],
     "why": "各种格式互转：JSON↔TypeScript↔GraphQL↔SQL…"},
    {"name": "ExplainShell", "url": "https://explainshell.com", "folders": ["开发工具", "效率工具"],
     "why": "任意 shell 命令逐段解释，看懂别人的命令"},

    # ===== 开发工具/编程学习 =====
    {"name": "freeCodeCamp", "url": "https://www.freecodecamp.org", "folders": ["开发工具", "编程学习"],
     "why": "免费系统课程 + 项目实战 + 免费认证"},
    {"name": "Roadmap.sh", "url": "https://roadmap.sh", "folders": ["开发工具", "编程学习"],
     "why": "前端/后端/DevOps/AI 等各方向可视化学习路线图"},
    {"name": "The Odin Project", "url": "https://www.theodinproject.com", "folders": ["开发工具", "编程学习"],
     "why": "开源全栈课程，以做真项目为核心"},
    {"name": "Exercism", "url": "https://exercism.org", "folders": ["开发工具", "编程学习"],
     "why": "60+ 语言刷题，有人工导师点评代码"},
    {"name": "GeeksforGeeks", "url": "https://www.geeksforgeeks.org", "folders": ["开发工具", "编程学习"],
     "why": "算法题解 + 教程大全，搜索友好"},
    {"name": "StackBlitz", "url": "https://stackblitz.com", "folders": ["开发工具", "编程学习"],
     "why": "浏览器内全栈开发沙箱，分享链接即环境"},

    # ===== 开发工具/代码托管 =====
    {"name": "GitLab", "url": "https://gitlab.com", "folders": ["开发工具", "代码托管"],
     "why": "仓库 + CI/CD 一体，免费私有仓库"},
    {"name": "Sourcegraph", "url": "https://sourcegraph.com", "folders": ["开发工具", "代码托管"],
     "why": "大规模代码搜索与导航，读开源项目神器"},

    # ===== 前端与设计/前端教程 =====
    {"name": "Can I Use", "url": "https://caniuse.com", "folders": ["前端与设计", "前端教程"],
     "why": "浏览器特性兼容性速查表"},
    {"name": "Tailwind CSS", "url": "https://tailwindcss.com", "folders": ["前端与设计", "前端教程"],
     "why": "原子化 CSS 框架官方文档"},
    {"name": "web.dev", "url": "https://web.dev", "folders": ["前端与设计", "前端教程"],
     "why": "Google 前端性能 / PWA / 最佳实践"},
    {"name": "CSS-Tricks", "url": "https://css-tricks.com", "folders": ["前端与设计", "前端教程"],
     "why": "CSS 技巧长文，图解清楚"},
    {"name": "Smashing Magazine", "url": "https://www.smashingmagazine.com", "folders": ["前端与设计", "前端教程"],
     "why": "前端/设计/UX 深度文章"},

    # ===== 前端与设计/图标与logo =====
    {"name": "Iconify", "url": "https://iconify.design", "folders": ["前端与设计", "图标与logo"],
     "why": "10 万+ 开源图标统一接口，一套 API 用所有图标集"},
    {"name": "Heroicons", "url": "https://heroicons.com", "folders": ["前端与设计", "图标与logo"],
     "why": "Tailwind 系精美 SVG 图标"},
    {"name": "unDraw", "url": "https://undraw.co", "folders": ["前端与设计", "图标与logo"],
     "why": "免费可商用插画，可改主色"},

    # ===== 前端与设计/配色 =====
    {"name": "Coolors", "url": "https://coolors.co", "folders": ["前端与设计", "配色"],
     "why": "一键生成/探索配色方案"},

    # ===== AI 工具/开发平台 =====
    {"name": "OpenRouter", "url": "https://openrouter.ai", "folders": ["AI 工具", "开发平台"],
     "why": "一个 API 调用全市场大模型，比价 + 兜底"},
    {"name": "硅基流动", "url": "https://siliconflow.cn", "folders": ["AI 工具", "开发平台"],
     "why": "国内模型 API 平台，便宜且稳定"},
    {"name": "魔搭 ModelScope", "url": "https://modelscope.cn", "folders": ["AI 工具", "开发平台"],
     "why": "阿里模型社区：模型/数据集/在线体验"},
    {"name": "Hugging Face", "url": "https://huggingface.co", "folders": ["AI 工具", "开发平台"],
     "why": "全球最大模型/数据集生态"},
    {"name": "v0", "url": "https://v0.dev", "folders": ["AI 工具", "开发平台"],
     "why": "AI 对话生成前端页面，可导出代码"},
    {"name": "Bolt", "url": "https://bolt.new", "folders": ["AI 工具", "开发平台"],
     "why": "浏览器内 AI 全栈开发，直接跑起来"},
    {"name": "Cursor 文档", "url": "https://docs.cursor.com", "folders": ["AI 工具", "开发平台"],
     "why": "AI 编辑器官方文档"},
    {"name": "Claude Code 文档", "url": "https://code.claude.com/docs", "folders": ["AI 工具", "开发平台"],
     "why": "Claude Code 官方文档（你正在用的工具）"},
    {"name": "Aider", "url": "https://aider.chat", "folders": ["AI 工具", "开发平台"],
     "why": "终端 AI 结对编程，git 仓库级协作"},

    # ===== AI 工具/生图与模型 =====
    {"name": "Civitai", "url": "https://civitai.com", "folders": ["AI 工具", "生图与模型"],
     "why": "Stable Diffusion 模型/LoRA 最大社区"},
    {"name": "PromptHero", "url": "https://prompthero.com", "folders": ["AI 工具", "生图与模型"],
     "why": "提示词搜索引擎，抄作业圣地"},

    # ===== 建模美术/材质与HDR =====
    {"name": "ShareTextures", "url": "https://www.sharetextures.com", "folders": ["建模美术", "材质与HDR"],
     "why": "免费 PBR 贴图（中文站，全免费商用）"},
    {"name": "3D Textures", "url": "https://3dtextures.me", "folders": ["建模美术", "材质与HDR"],
     "why": "免费 PBR 材质库"},
    {"name": "BlenderKit", "url": "https://www.blenderkit.com", "folders": ["建模美术", "材质与HDR"],
     "why": "Blender 插件，软件内直接搜索/安装资产"},
    {"name": "Substance 3D Assets", "url": "https://substance3d.adobe.com/assets", "folders": ["建模美术", "材质与HDR"],
     "why": "Adobe 官方材质资产库"},

    # ===== 建模美术/模型与动画 =====
    {"name": "CGTrader", "url": "https://www.cgtrader.com", "folders": ["建模美术", "模型与动画"],
     "why": "商业/免费 3D 模型市场"},
    {"name": "FAB", "url": "https://www.fab.com", "folders": ["建模美术", "模型与动画"],
     "why": "Epic 官方模型/资产市场（UE 生态）"},
    {"name": "TurboSquid", "url": "https://www.turbosquid.com", "folders": ["建模美术", "模型与动画"],
     "why": "老牌 3D 模型市场，量大"},

    # ===== 建模美术/建模教程 =====
    {"name": "Blender Guru", "url": "https://www.blenderguru.com", "folders": ["建模美术", "建模教程"],
     "why": "甜甜圈教程的 Blender 大神"},

    # ===== 游戏/游戏工具 =====
    {"name": "itch.io", "url": "https://itch.io", "folders": ["游戏", "游戏工具"],
     "why": "独立游戏 + 免费游戏资产（素材/音乐/美术）"},
    {"name": "Nexus Mods", "url": "https://www.nexusmods.com", "folders": ["游戏", "游戏工具"],
     "why": "主流 Mod 下载站"},
    {"name": "Mod DB", "url": "https://www.moddb.com", "folders": ["游戏", "游戏工具"],
     "why": "老牌 Mod 社区"},
    {"name": "CurseForge", "url": "https://www.curseforge.com", "folders": ["游戏", "游戏工具"],
     "why": "MC 等游戏 Mod 整合平台"},

    # ===== 系统网络/系统与运维 =====
    {"name": "Vercel", "url": "https://vercel.com", "folders": ["系统网络", "系统与运维"],
     "why": "前端零配置部署，免费额度够个人用"},
    {"name": "Netlify", "url": "https://www.netlify.com", "folders": ["系统网络", "系统与运维"],
     "why": "静态站点托管 + 表单/函数"},
    {"name": "Cloudflare", "url": "https://www.cloudflare.com", "folders": ["系统网络", "系统与运维"],
     "why": "CDN/DNS/Worker/隧道全家桶"},
    {"name": "Docker Hub", "url": "https://hub.docker.com", "folders": ["系统网络", "系统与运维"],
     "why": "官方容器镜像仓库"},

    # ===== 学习考试/课程平台 =====
    {"name": "OSSU 计算机科学", "url": "https://github.com/ossu/computer-science",
     "folders": ["学习考试", "课程平台"],
     "why": "开源版 CS 本科课程路径，名校公开课合集"},
]


def by_folder():
    """按目标文件夹分组的目录 {路径: [条目]}。"""
    groups = {}
    for r in RECOMMEND:
        groups.setdefault("/".join(r["folders"]), []).append(r)
    return groups


def normalize_url(u):
    return (u or "").strip().rstrip("/").lower()


def select(add_all=False, names=None):
    """筛选条目：--all 全选；否则按名称子串匹配（中文或英文名均可）。"""
    if add_all:
        return list(RECOMMEND)
    sel = []
    for r in RECOMMEND:
        for n in (names or []):
            if n.strip().lower() in r["name"].lower():
                sel.append(r)
                break
    return sel


def to_add_json(entries):
    return [{"name": r["name"], "url": r["url"], "folders": r["folders"]}
            for r in entries]


# ===== 失效检测（实时性/准确性） =====
# HEAD 优先（省流量）；403/405/501 不代表站点死亡（很多站禁 HEAD），改用 GET 重试一次。
# 判定失效: 连接失败（dead:*）或 404/410/451/5xx。
import concurrent.futures
import urllib.error
import urllib.request

_UA = ("Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
       "bookmark-organizer recommend-check")


def check_one(entry, timeout=12):
    """检测单个条目。返回 (name, url, status, code)。

    status 三类:
      ok / HTTP xxx  —— 可达（HTTP 状态码见 code）
      net:xxx        —— 网络层失败（超时/DNS/TLS），≠ 站点死亡（防火墙/线路问题）
      HTTP 404/410   —— 站点有响应但内容没了 = 真失效
    """
    url = entry["url"]

    def open_req(method):
        req = urllib.request.Request(
            url, method=method, headers={"User-Agent": _UA})
        return urllib.request.urlopen(req, timeout=timeout)

    try:
        with open_req("HEAD") as resp:
            code = resp.status
            return (entry["name"], url,
                    "ok" if code < 400 else f"HTTP {code}", code)
    except urllib.error.HTTPError as e:
        if e.code in (403, 405, 501):  # HEAD 被拒 → GET 重试
            try:
                with open_req("GET") as resp:
                    code = resp.status
                    return (entry["name"], url,
                            "ok" if code < 400 else f"HTTP {code}", code)
            except urllib.error.HTTPError as e2:
                return (entry["name"], url, f"HTTP {e2.code}", e2.code)
            except Exception as e2:
                return (entry["name"], url, f"net:{type(e2).__name__}", None)
        return (entry["name"], url, f"HTTP {e.code}", e.code)
    except Exception as e:
        # 网络层失败 ≠ 站点死亡 → GET 重试一次排除瞬时抖动
        try:
            with open_req("GET") as resp:
                code = resp.status
                return (entry["name"], url,
                        "ok" if code < 400 else f"HTTP {code}", code)
        except urllib.error.HTTPError as e2:
            return (entry["name"], url, f"HTTP {e2.code}", e2.code)
        except Exception as e2:
            reason = getattr(e, "reason", e) or e
            return (entry["name"], url, f"net:{type(reason).__name__}", None)


def is_dead(result):
    """(name, url, status, code) -> 是否判定为失效（只有站点明确响应 404/410/451/5xx）。
    net:*（超时/DNS/TLS）不算死亡——站点本身可能活着，只是当前网络不可达。"""
    status = result[2] or ""
    if status.startswith("HTTP"):
        code = result[3] or 0
        return code in (404, 410, 451) or code >= 500
    return False


def is_unreachable(result):
    """网络层不可达（非站点死亡）。"""
    return (result[2] or "").startswith("net:")


def check_sites(entries=None, workers=10, timeout=12):
    """并发体检。返回 [(name, url, status, code)]（顺序与输入一致）。"""
    entries = entries if entries is not None else RECOMMEND
    with concurrent.futures.ThreadPoolExecutor(max_workers=workers) as ex:
        return list(ex.map(lambda e: check_one(e, timeout), entries))


if __name__ == "__main__":
    print(json.dumps(to_add_json(RECOMMEND), ensure_ascii=False, indent=2))
