#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""执行器：把 reorg_plan.json 应用到 Edge Bookmarks 文件

用法: python apply_plan.py <源文件> <目标文件>

设计要点:
- 复用原书签 dict（保留 guid/id/date_added/date_last_used/show_icon 等元数据）
- 新文件夹 dict 按 Edge 151 格式生成（uuid4 guid、递增数字 id、WebKit 时间戳）
- 删除顶层 checksum/sync_metadata（Edge 启动时自行重建）
- 顶层文件夹按固定顺序排列；「娱乐/资源」6 个子分类按固定顺序
- 未消费的书签兜底保留到原根的「_未归类」文件夹（正常应为 0）
"""
import json
import sys
import time
import uuid

PLAN = r"E:\NET Program\bookmark-organizer\reorg_plan.json"
WEBKIT_EPOCH = 11644473600

# 顶层固定顺序（按使用频率/重要度），回收站垫底
ORDER = ["开发工具", "建模美术", "AI 工具", "前端与设计", "游戏",
         "娱乐", "学习考试", "系统网络", "回收站"]
# 指定父路径下的子文件夹固定顺序
SUBORDER = {
    "娱乐/资源": ["动画里番", "漫画本子", "视频", "游戏与模组", "图片Coser", "社区与搜索"],
}


def webkit_ts():
    return str(int((time.time() + WEBKIT_EPOCH) * 1_000_000))


def build_index(roots):
    """old_path|url -> [原始书签 dict, ...]（同路径同名同 URL 可能重复）"""
    idx = {}

    def walk(children, folders):
        for c in children:
            if c.get("type") == "folder":
                walk(c.get("children", []), folders + [c.get("name") or ""])
            else:
                key = "/".join(folders + [c.get("name") or ""]) + "|" + (c.get("url") or "")
                idx.setdefault(key, []).append(c)

    for rn, r in roots.items():
        walk(r.get("children", []), [rn])
    return idx


def max_id(roots):
    m = 0

    def walk(children):
        nonlocal m
        for c in children:
            try:
                m = max(m, int(c.get("id", 0)))
            except (TypeError, ValueError):
                pass
            if c.get("type") == "folder":
                walk(c.get("children", []))

    for r in roots.values():
        walk(r.get("children", []))
        try:
            m = max(m, int(r.get("id", 0)))
        except (TypeError, ValueError):
            pass
    return m


def normalize(node, parent_path):
    """按 ORDER/SUBORDER 重排子文件夹顺序"""
    keys = [k for k in node.keys() if k != "_items"]
    order = ORDER if not parent_path else SUBORDER.get(parent_path, [])
    keys = [k for k in order if k in keys] + [k for k in keys if k not in order]
    out = {}
    if "_items" in node:
        out["_items"] = node["_items"]
    for k in keys:
        out[k] = normalize(node[k], (parent_path + "/" + k) if parent_path else k)
    return out


def apply(src_path, dst_path):
    d = json.load(open(src_path, encoding="utf-8"))
    plan = json.load(open(PLAN, encoding="utf-8"))
    roots = d["roots"]
    idx = build_index(roots)
    consumed = {}
    used_ids = set()
    tree = {}
    unconsumed = []

    for p in plan:
        key = p["old"] + "|" + p["url"]
        cands = idx.get(key, [])
        k = consumed.get(key, 0)
        if k >= len(cands):
            unconsumed.append(key)
            continue
        item = cands[k]
        consumed[key] = k + 1
        used_ids.add(id(item))
        if p["rename"]:
            item["name"] = p["rename"]
        t = tree
        for seg in p["folders"]:
            t = t.setdefault(seg, {})
        t.setdefault("_items", []).append(item)

    tree = normalize(tree, "")

    nid = [max_id(roots)]
    ts = webkit_ts()

    def build(node):
        out = []
        for k, v in node.items():
            if k == "_items":
                out.extend(v)
            else:
                nid[0] += 1
                out.append({
                    "children": build(v),
                    "date_added": ts,
                    "date_modified": ts,
                    "guid": str(uuid.uuid4()),
                    "id": str(nid[0]),
                    "name": k,
                    "type": "folder",
                })
        return out

    roots["bookmark_bar"]["children"] = build(tree)
    roots["bookmark_bar"]["date_modified"] = ts

    # 兜底：未消费的书签保留到原根的「_未归类」
    leftovers = {}

    def collect(children, rn):
        for c in children:
            if c.get("type") == "folder":
                collect(c.get("children", []), rn)
            elif id(c) not in used_ids:
                leftovers.setdefault(rn, []).append(c)

    for rn in list(roots.keys()):
        if rn == "bookmark_bar":
            continue
        r = roots[rn]
        collect(r.get("children", []), rn)
        if rn in leftovers:
            nid[0] += 1
            r["children"] = [{
                "children": leftovers[rn],
                "date_added": ts, "date_modified": ts,
                "guid": str(uuid.uuid4()), "id": str(nid[0]),
                "name": "_未归类", "type": "folder",
            }]
        else:
            r["children"] = []

    out = {"roots": roots, "version": d.get("version", 1)}
    with open(dst_path, "w", encoding="utf-8") as f:
        json.dump(out, f, ensure_ascii=False, indent=2)

    print(f"已写入: {dst_path}")
    print(f"计划 {len(plan)} 条 | 未消费 {len(unconsumed)} | "
          f"兜底未归类 {sum(len(v) for v in leftovers.values())} | 新建文件夹 {nid[0] - max_id(roots)}")
    if unconsumed:
        print("!! 未消费条目(前10):")
        for k in unconsumed[:10]:
            print("   ", k[:120])


if __name__ == "__main__":
    if len(sys.argv) != 3:
        print("用法: python apply_plan.py <源文件> <目标文件>")
        sys.exit(1)
    apply(sys.argv[1], sys.argv[2])
