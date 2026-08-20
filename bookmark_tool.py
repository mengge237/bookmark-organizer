#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""收藏夹整理工具箱（统一入口）

用法:
  python bookmark_tool.py status  [--file PATH]   当前收藏夹结构总览（书签数/分类/回收站）
  python bookmark_tool.py backup  [--file PATH]   备份当前 Bookmarks 文件到 backup/
  python bookmark_tool.py plan    [--file PATH]   生成整理方案（审核 markdown + 机器 JSON）
  python bookmark_tool.py apply   [--file PATH]   应用方案（先自动备份；须先关闭 Edge）
  python bookmark_tool.py restore [--file PATH] [--backup NAME]   从 backup/ 恢复（默认最新）
  python bookmark_tool.py push    [--file PATH] [--wait-upload SEC] [--no-relaunch]
                                                  走官方 API（临时扩展）把整理结果推上云端，同步可保持开启
  python bookmark_tool.py recommend               浏览开发者推荐网站目录（写入 推荐网站目录.md）
  python bookmark_tool.py recommend --check       体检全部推荐站点是否失效
  python bookmark_tool.py recommend --on [--all|--names KEY]   开启推荐模式：添加推荐书签并推上云端
  python bookmark_tool.py recommend --off         关闭推荐模式：只删推荐模式添加的书签并推上云端

推荐模式说明:
  · 开关状态 + 已添加清单（name/url/guid/添加时间）持久化在 recommend_state.json —— 有迹可循，
    关闭时按 guid 精确删除（URL 兜底），绝不误删你自己的书签。
  · --on 会先体检（可 --skip-check 跳过），自动跳过失效站点；--check 可随时单独体检。
  · 目录数据在 recommend_sites.py 的 RECOMMEND 列表，加新站点 = 加一条 dict（可扩展）。

默认 --file 为真实 profile 的 Bookmarks。
规则在 reorg_plan.py 的 RULES 列表里维护；plan 会列出未匹配的书签，供新增规则参考。
"""
import argparse
import datetime
import glob
import json
import os
import shutil
import subprocess
import sys
import time

REAL = r"C:\Users\Lenovo\AppData\Local\Microsoft\Edge\User Data\Default\Bookmarks"
BASE = os.path.dirname(os.path.abspath(__file__))
BACKUP_DIR = os.path.join(BASE, "backup")
PLAN_MD = os.path.join(BASE, "收藏夹重组方案.md")
PLAN_JSON = os.path.join(BASE, "reorg_plan.json")
RECOMMEND_MD = os.path.join(BASE, "推荐网站目录.md")
STATE_FILE = os.path.join(BASE, "recommend_state.json")
EXT_DIR = os.path.join(BASE, "ext")
EXT_PLAN = os.path.join(EXT_DIR, "plan.json")
EXT_ADD = os.path.join(EXT_DIR, "add.json")
EXT_REMOVE = os.path.join(EXT_DIR, "remove.json")
EDGE_CANDIDATES = (
    r"C:\Program Files (x86)\Microsoft\Edge\Application\msedge.exe",
    r"C:\Program Files\Microsoft\Edge\Application\msedge.exe",
)

sys.path.insert(0, BASE)
import reorg_plan  # noqa: E402
import apply_plan  # noqa: E402
import recommend_sites  # noqa: E402


def edge_running():
    try:
        out = subprocess.run(
            ["tasklist", "/FO", "CSV", "/NH", "/FI", "IMAGENAME eq msedge.exe"],
            capture_output=True, text=True, timeout=15)
        return "msedge.exe" in out.stdout.lower()
    except Exception:
        return False


def ts():
    return datetime.datetime.now().strftime("%Y%m%d-%H%M%S")


def find_edge():
    for p in EDGE_CANDIDATES:
        if os.path.exists(p):
            return p
    try:
        out = subprocess.run(["where", "msedge"], capture_output=True, text=True)
        for line in out.stdout.splitlines():
            line = line.strip()
            if line.lower().endswith("msedge.exe"):
                return line
    except Exception:
        pass
    return None


def kill_edge():
    """关闭全部 Edge 进程（先优雅关闭再强制）；返回是否已确认全部退出。"""
    if not edge_running():
        return True
    subprocess.run(["taskkill", "/IM", "msedge.exe"],
                   capture_output=True, text=True)
    deadline = time.time() + 10
    while edge_running() and time.time() < deadline:
        time.sleep(1)
    if edge_running():
        subprocess.run(["taskkill", "/F", "/IM", "msedge.exe"],
                       capture_output=True, text=True)
        deadline = time.time() + 20
        while edge_running() and time.time() < deadline:
            time.sleep(1)
    return not edge_running()


def norm(u):
    return (u or "").strip().rstrip("/").lower()


def plan_structure():
    """方案 JSON → (顶层文件夹→书签数, 总书签数)。"""
    plan = json.load(open(PLAN_JSON, encoding="utf-8"))
    top = {}
    for e in plan:
        top[e["folders"][0]] = top.get(e["folders"][0], 0) + 1
    return top, len(plan)


def file_structure(path):
    """Bookmarks 文件 → (顶层文件夹→书签数, 书签栏直接书签数, other 根条数)。"""
    d = json.load(open(path, encoding="utf-8"))
    bb = d["roots"]["bookmark_bar"]

    def count(n):
        c = 0
        for ch in n.get("children", []):
            c += 1 if ch.get("type") != "folder" else count(ch)
        return c

    tops = {}
    for c in bb.get("children", []):
        if c.get("type") == "folder":
            tops[c["name"]] = count(c)
    direct = sum(1 for c in bb.get("children", []) if c.get("type") != "folder")
    other = len(d["roots"].get("other", {}).get("children", []))
    return tops, direct, other


def matches_plan(path, expected):
    try:
        tops, direct, other = file_structure(path)
    except Exception:
        return False
    return other == 0 and direct == 0 and tops == expected


def load_state():
    try:
        with open(STATE_FILE, encoding="utf-8") as f:
            return json.load(f)
    except Exception:
        return {"enabled": False, "added": [], "checks": []}


def save_state(st):
    with open(STATE_FILE, "w", encoding="utf-8") as f:
        json.dump(st, f, ensure_ascii=False, indent=2)


def index_file(path):
    """Bookmarks 文件 → (url 集合, guid→顶层文件夹, url→[(guid, 顶层, 是否书签栏)])。
    顶层 = 书签栏内该节点所属最外层文件夹名（bar 直连/other 内为 None）；
    遍历顺序与文件顺序一致，与扩展侧（getTree 遍历序）保持同构。"""
    d = json.load(open(path, encoding="utf-8"))
    url_set = set()
    guid_top = {}
    url_map = {}

    def walk(children, top, in_bar):
        for c in children:
            if c.get("type") == "folder":
                walk(c.get("children", []),
                     (top or c["name"]) if in_bar else top, in_bar)
            else:
                u = norm(c.get("url", ""))
                url_set.add(u)
                url_map.setdefault(u, []).append((c.get("guid"), top, in_bar))
                if c.get("guid"):
                    guid_top[c["guid"]] = top

    for rn, r in d["roots"].items():
        walk(r.get("children", []), None, rn == "bookmark_bar")
    return url_set, guid_top, url_map


def expected_structure(path, adds=None, removes=None):
    """期望顶层结构 = 方案 + 实际会新增 − 实际会删除（扩展侧同算法计算，两侧一致才通过校验）。

    扣减规则：删除的书签只有"在方案中有对应条目、且删掉后方案覆盖不足"时才扣减
    （deficit = max(0, 方案中该 URL 数 − (文件中该 URL 数 − 删除数))）。
    推荐书签不在方案里 → deficit 为 0 → 不扣减，删完正好回到方案结构。
    """
    expected, _ = plan_structure()
    if not adds and not removes:
        return expected
    url_set, guid_top, url_map = index_file(path)
    for a in (adds or []):
        if norm(a["url"]) not in url_set:
            expected[a["folders"][0]] = expected.get(a["folders"][0], 0) + 1
    if not removes:
        return expected
    from collections import Counter
    plan = json.load(open(PLAN_JSON, encoding="utf-8"))
    plan_counts = Counter(norm(e["url"]) for e in plan)
    file_counts = Counter({u: len(lst) for u, lst in url_map.items()})
    present = []  # [(norm_url, 顶层)]
    for r in removes:
        top, u = None, None
        if r.get("guid") and r["guid"] in guid_top:
            top = guid_top[r["guid"]]
            u = next((url for url, lst in url_map.items()
                      if any(x[0] == r["guid"] for x in lst)), None)
        else:
            lst = url_map.get(norm(r.get("url", "")), [])
            hit = next((x for x in lst if x[2]), lst[0] if lst else None)
            if hit:
                top, u = hit[1], norm(r.get("url", ""))
        if top:
            present.append((u, top))
    removed_counts = Counter(u for u, t in present)
    deficit = {u: max(0, plan_counts.get(u, 0)
                      - (file_counts.get(u, 0) - removed_counts.get(u, 0)))
               for u in removed_counts}
    for u, top in present:
        if deficit.get(u, 0) > 0:
            deficit[u] -= 1
            expected[top] = expected.get(top, 0) - 1
            if expected[top] <= 0:
                del expected[top]
    return expected


def find_added_guids(path, adds):
    """运行后按 URL 从文件里找回新书签的 guid —— 登记来源（有迹可循）。"""
    _, _, url_map = index_file(path)
    now = datetime.datetime.now().isoformat(timespec="seconds")
    out = []
    for a in adds:
        lst = url_map.get(norm(a["url"]), [])
        hit = next((x for x in lst if x[2]), lst[0] if lst else None)
        if hit and hit[0]:
            out.append({"name": a["name"], "url": a["url"],
                        "folders": a["folders"], "guid": hit[0],
                        "added_at": now})
    return out


def cmd_status(path):
    d = json.load(open(path, encoding="utf-8"))
    bb = d["roots"]["bookmark_bar"]

    def walk(n, depth):
        rows = []
        for c in n.get("children", []):
            if c.get("type") == "folder":
                cnt = sum(1 for x in c.get("children", []) if x.get("type") != "folder")
                rows.append((depth, "📁 " + c["name"], cnt))
                rows.extend(walk(c, depth + 1))
            else:
                rows.append((depth, c["name"][:50], c.get("url", "")[:60]))
        return rows

    rows = walk(bb, 0)
    total = sum(1 for r in rows if not r[1].startswith("📁"))
    for depth, name, extra in rows:
        if name.startswith("📁"):
            print("  " * depth + f"{name} ({extra} 直属于此)")
        else:
            print("  " * depth + f"· {name}")
    print(f"\n书签总数: {total}")
    for rn in ("other", "synced"):
        print(f"{rn}: {len(d['roots'].get(rn, {}).get('children', []))} 条")
    print("同步状态提示: 用 push 推上云端后同步可保持开启；直接改文件则必须关闭收藏夹同步，否则云端会合并回滚。")


def cmd_backup(path):
    os.makedirs(BACKUP_DIR, exist_ok=True)
    dst = os.path.join(BACKUP_DIR, f"Bookmarks.{ts()}.json")
    shutil.copyfile(path, dst)
    print(f"已备份: {dst}")


def cmd_plan(path):
    bookmarks, plan, unmatched, conflicts = reorg_plan.main(
        src=path, out_md=PLAN_MD, out_json=PLAN_JSON)
    if unmatched:
        print("\n未匹配书签（供新增规则参考）:")
        for b in unmatched:
            print(f"  {b['old']}\n    {b['url'][:100]}")


def cmd_apply(path, force=False):
    if edge_running() and not force:
        print("⚠ Edge 正在运行！请先关闭 Edge（运行中改文件会被覆盖）。")
        try:
            if input("仍要继续？(y/N) ").strip().lower() != "y":
                return
        except EOFError:
            print("非交互模式，已中止。请先关闭 Edge 再执行（或加 --force）。")
            return
    cmd_backup(path)
    apply_plan.apply(path, path)
    print("应用完成。重新打开 Edge 后可用 status 验证。")


def cmd_restore(path, name=None, force=False):
    os.makedirs(BACKUP_DIR, exist_ok=True)
    backups = sorted(glob.glob(os.path.join(BACKUP_DIR, "*.json")))
    if not backups:
        print("backup/ 目录下没有备份文件。")
        return
    if name:
        src = name if (os.sep in name or "/" in name) else os.path.join(BACKUP_DIR, name)
    else:
        src = backups[-1]
    if edge_running() and not force:
        print("⚠ Edge 正在运行！恢复前请先关闭 Edge（或加 --force）。已中止。")
        return
    shutil.copyfile(src, path)
    print(f"已从 {src} 恢复到 {path}")


def _confirm(prompt, force):
    if force:
        return True
    try:
        return input(prompt).strip().lower() == "y"
    except EOFError:
        print("非交互模式，请加 --force。")
        return False


def cmd_push(args, adds=None, removes=None):
    """通过临时 MV3 扩展（官方 chrome.bookmarks API）把结构推上云端。

    官方 API 的改动会被同步引擎当作正常用户操作上传，云端旧结构不再合并回滚。
    adds/removes: 推荐模式的新增/删除清单（与扩展侧 plan.json/add.json/remove.json 对应）。
    流程: 关 Edge → 备份 → 加载扩展启动 → 扩展应用方案 → 等同步上传 →
          普通重启验证云端没有回滚。返回 True=成功（--no-relaunch 时以文件校验为准）。
    """
    if not os.path.exists(PLAN_JSON):
        print("没有 reorg_plan.json，请先运行 plan。")
        return False
    if not os.path.exists(os.path.join(EXT_DIR, "manifest.json")) or \
       not os.path.exists(os.path.join(EXT_DIR, "service_worker.js")):
        print("ext/ 缺少扩展文件（manifest.json / service_worker.js）。")
        return False
    edge = find_edge()
    if not edge:
        print("找不到 msedge.exe。")
        return False
    if edge_running() and not _confirm("⚠ 将关闭所有 Edge 窗口（含未保存的页面）！继续？(y/N) ",
                                       args.force):
        return False
    if not kill_edge():
        print("✗ 无法关闭 Edge，中止。")
        return False

    cmd_backup(args.file)
    shutil.copyfile(PLAN_JSON, EXT_PLAN)
    with open(EXT_ADD, "w", encoding="utf-8") as f:
        json.dump(adds or [], f, ensure_ascii=False)
    with open(EXT_REMOVE, "w", encoding="utf-8") as f:
        json.dump(removes or [], f, ensure_ascii=False)
    expected, total = plan_structure()
    ops = f"方案: {total} 条书签"
    if adds:
        ops += f" + 新增 {len(adds)} 条推荐书签"
    if removes:
        ops += f" − 删除 {len(removes)} 条推荐书签"
    if adds or removes:
        expected = expected_structure(args.file, adds, removes)
    print(f"{ops} → 顶层 {expected}")

    launch = [edge, f"--load-extension={EXT_DIR}"]
    if args.edge_args:
        launch += args.edge_args.split()
    print(f"启动 Edge（加载扩展）: {' '.join(launch)}")
    subprocess.Popen(launch, close_fds=True)

    print("等待扩展应用（最长 150s）...")
    deadline = time.time() + 150
    while time.time() < deadline:
        if matches_plan(args.file, expected):
            print("✓ Bookmarks 文件已变为目标结构。")
            break
        time.sleep(5)
    else:
        print("✗ 超时未完成。可能原因: 扩展未加载 / 方案与当前书签不匹配 / 同步冲突。")
        print("  可查看 ext 的 chrome.storage.local 或 favorites_diagnostic.log 排查。")
        return False

    if args.no_relaunch:
        print("完成（未做重启验证）。")
        return True

    print(f"等待同步上传（{args.wait_upload}s）...")
    time.sleep(args.wait_upload)

    print("重启 Edge（普通启动，验证云端没有回滚）...")
    kill_edge()
    subprocess.Popen([edge], close_fds=True)
    deadline = time.time() + 60
    ok = False
    while time.time() < deadline:
        if matches_plan(args.file, expected):
            ok = True
            break
        time.sleep(5)
    if ok:
        print("✓✓ 云端已接受新结构——同步开启状态下整理持久有效。")
        return True
    print("✗ 重启后结构被回滚——上传未完成。可加大 --wait-upload 重试。")
    return False


def cmd_recommend(args):
    if args.check:
        print(f"体检 {len(recommend_sites.RECOMMEND)} 个推荐站点（并发，约 1 分钟）...")
        results = recommend_sites.check_sites()
        dead = [r for r in results if recommend_sites.is_dead(r)]
        unreachable = [r for r in results if recommend_sites.is_unreachable(r)]
        now = datetime.datetime.now().isoformat(timespec="seconds")
        st = load_state()
        st["checks"] = [
            {"name": r[0], "url": r[1], "status": r[2], "code": r[3], "checked_at": now}
            for r in results
        ]
        save_state(st)
        for name, url, status, code in results:
            r = (name, url, status, code)
            mark = "✗" if recommend_sites.is_dead(r) else (
                "⚠" if recommend_sites.is_unreachable(r) else "✓")
            print(f"  {mark} {name:<22s} {status:<16s} {url}")
        print(f"\n存活 {len(results) - len(dead) - len(unreachable)}/"
              f"{len(results)}；不可达(网络原因) {len(unreachable)}；失效 {len(dead)} 个。")
        if unreachable:
            print("不可达清单（不是站点死亡，可能是校园网/防火墙；--on 仍会添加，仅提示）:")
            for name, url, status, code in unreachable:
                print(f"  ⚠ {name}  {url}  ({status})")
        if dead:
            print("失效清单（--on 会自动跳过；也可从 recommend_sites.py 删除该条目）:")
            for name, url, status, code in dead:
                print(f"  ✗ {name}  {url}  ({status})")
        return

    if args.off:
        st = load_state()
        added = st.get("added") or []
        if not added:
            print("推荐模式当前没有登记的书签（recommend_state.json 的 added 为空）。")
            return
        removes = [{"guid": a.get("guid"), "url": a["url"]} for a in added]
        print(f"即将关闭推荐模式并删除 {len(removes)} 个推荐书签（只删登记的，有迹可循）:")
        for a in added:
            print(f"  - {a.get('name')}  {a['url']}")
        if not _confirm("继续？(y/N) ", args.force):
            return
        if not cmd_push(args, adds=None, removes=removes):
            print("✗ 关闭失败（未推上云端），state 未改动，推荐书签仍在。")
            return
        st["enabled"] = False
        st["added"] = []
        st["off_at"] = datetime.datetime.now().isoformat(timespec="seconds")
        save_state(st)
        print("✓ 推荐模式已关闭，推荐书签已删除并同步云端。")
        return

    if not args.on:
        # 目录视图：分组 + 已收藏标记 + 开关状态 → 推荐网站目录.md
        url_set = set()
        try:
            url_set, _, _ = index_file(args.file)
        except Exception:
            pass
        st = load_state()
        lines = ["# 开发者推荐网站目录", "",
                 f"共 {len(recommend_sites.RECOMMEND)} 个推荐站点（✓ = 已在收藏夹）。",
                 f"推荐模式: {'开启' if st.get('enabled') else '关闭'}；"
                 f"已登记可追溯书签 {len(st.get('added') or [])} 个。"]
        checks = st.get("checks") or []
        if checks:
            dead = [c for c in checks if recommend_sites.is_dead(
                (c.get("name"), c.get("url"), c.get("status"), c.get("code")))]
            lines.append(f"最近体检: {checks[0].get('checked_at', '?')}；失效 {len(dead)} 个。")
        lines.append("")
        for path, entries in sorted(recommend_sites.by_folder().items()):
            lines.append(f"## {path}")
            lines.append("")
            for e in entries:
                mark = "✓" if recommend_sites.normalize_url(e["url"]) in url_set else "·"
                lines.append(f"- {mark} **{e['name']}** — {e['url']}")
                lines.append(f"  - {e['why']}")
            lines.append("")
        md = "\n".join(lines)
        with open(RECOMMEND_MD, "w", encoding="utf-8") as f:
            f.write(md)
        print(md)
        print(f"已写入 {RECOMMEND_MD}。")
        print("用法: recommend --on 开启（自动跳过失效站，可 --names 筛选）；"
              "recommend --off 关闭并删除；recommend --check 体检。")
        return

    # --on：全选或按名选择 → 体检跳过失效 → 推上云端 → 登记 guid
    sel = recommend_sites.select(add_all=args.all or not args.names, names=args.names)
    if not sel:
        print("没有选中任何网站（--names 没匹配上？）。")
        return
    if not args.skip_check:
        print(f"先体检 {len(sel)} 个站点...")
        results = recommend_sites.check_sites(sel)
        dead = {r[1]: r for r in results if recommend_sites.is_dead(r)}
        unreachable = {r[1]: r for r in results if recommend_sites.is_unreachable(r)}
        if unreachable:
            for name, url, status, code in unreachable.values():
                print(f"  ⚠ 网络不可达（站点未死，仍会添加）: {name}  {url}  ({status})")
        if dead:
            for name, url, status, code in dead.values():
                print(f"  ✗ 跳过失效: {name}  {url}  ({status})")
            sel = [e for e in sel if e["url"] not in dead]
        if not sel:
            print("全部失效，未添加。")
            return
    adds = recommend_sites.to_add_json(sel)
    print(f"将添加 {len(adds)} 个推荐书签:")
    for a in adds:
        print(f"  + {a['name']}  →  {'/'.join(a['folders'])}")
    if not _confirm("继续？(y/N) ", args.force):
        return
    if not cmd_push(args, adds=adds, removes=None):
        print("✗ 添加失败（未推上云端），state 未改动。")
        return
    records = find_added_guids(args.file, adds)
    st = load_state()
    st["enabled"] = True
    st["added"] = records
    st["on_at"] = datetime.datetime.now().isoformat(timespec="seconds")
    save_state(st)
    print(f"✓ 推荐模式已开启：{len(records)} 个书签已添加并同步云端；来源已登记（--off 可一键删除）。")


def main():
    ap = argparse.ArgumentParser(description="收藏夹整理工具箱")
    ap.add_argument("command",
                    choices=["status", "backup", "plan", "apply", "restore", "push", "recommend"])
    ap.add_argument("--file", default=REAL, help="Bookmarks 文件路径（默认真实 profile）")
    ap.add_argument("--backup", default=None, help="restore 用：备份文件名或路径")
    ap.add_argument("--force", action="store_true",
                    help="apply/push/recommend 用：跳过 Edge 运行检查与交互确认")
    ap.add_argument("--edge-args", default=None,
                    help="push 用：附加 Edge 启动参数（空格分隔）")
    ap.add_argument("--wait-upload", type=int, default=90,
                    help="push 用：同步上传等待秒数（默认 90）")
    ap.add_argument("--no-relaunch", action="store_true",
                    help="push 用：跳过重启验证（调试 profile 用）")
    ap.add_argument("--on", action="store_true", help="recommend 用：开启推荐模式（添加推荐书签）")
    ap.add_argument("--off", action="store_true", help="recommend 用：关闭推荐模式（删除推荐书签）")
    ap.add_argument("--check", action="store_true", help="recommend 用：体检推荐站点是否失效")
    ap.add_argument("--all", action="store_true", help="recommend --on 用：全选目录")
    ap.add_argument("--names", action="append", default=None,
                    help="recommend --on 用：按名称关键词选择（可多次）")
    ap.add_argument("--skip-check", action="store_true", help="recommend --on 用：跳过添加前体检")
    args = ap.parse_args()
    {
        "status": lambda: cmd_status(args.file),
        "backup": lambda: cmd_backup(args.file),
        "plan": lambda: cmd_plan(args.file),
        "apply": lambda: cmd_apply(args.file, args.force),
        "restore": lambda: cmd_restore(args.file, args.backup, args.force),
        "push": lambda: cmd_push(args),
        "recommend": lambda: cmd_recommend(args),
    }[args.command]()


if __name__ == "__main__":
    main()
