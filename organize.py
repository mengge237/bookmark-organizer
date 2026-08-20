#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Edge 收藏夹整理脚本
- 把「其他收藏夹」的散落书签归入收藏夹栏的现有分类
- 全树去重（相同 URL 保留首次出现）
- 先备份再修改，输出变更报告

用法:
    python organize.py <源Bookmarks文件> <目标Bookmarks文件> [--dry-run]
"""
import json
import shutil
import sys
import os

# (url片段, 书签名, 目标文件夹路径) —— url片段用于定位书签
MOVES = [
    ("dlsite.com", "DLsite", ["娱乐"]),
    ("openweathermap.org", "OpenWeatherMap", ["常用工具"]),
    ("id.unity.cn", "Unity ID", ["开发工具"]),
    ("baijiahao.baidu.com", "C盘清理文章", ["教程"]),
    ("moegirl.org.cn", "萌娘百科-鸣潮图集", ["娱乐"]),
    ("account.jetbrains.com", "JetBrains Account", ["开发工具"]),
    ("natfrp.com", "SakuraFrp", ["工具"]),
    ("assetstore.u3d.cn", "Unity资源商店", ["开发工具"]),
    ("czzyv.com/movie", "厂长资源-电影", ["娱乐"]),  # 3 条逐个移动
]


def load(path):
    with open(path, encoding="utf-8") as f:
        return json.load(f)


def save(path, data):
    data.pop("checksum", None)  # Edge 启动时会重新计算
    with open(path, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)


def find_folder(children, name):
    for c in children:
        if c.get("type") == "folder" and c.get("name") == name:
            return c
    return None


def get_folder(root, path):
    node = root
    for name in path:
        node = find_folder(node.get("children", []), name)
        if node is None:
            raise KeyError(f"找不到文件夹: {name} (路径: {'/'.join(path)})")
    return node


def collect_url_nodes(children, acc):
    """按 DFS 顺序收集所有书签节点和它们的直接父列表"""
    for c in children:
        if c.get("type") == "url":
            acc.append((children, c))
        elif c.get("type") == "folder":
            collect_url_nodes(c.get("children", []), acc)


def main():
    src, dst = sys.argv[1], sys.argv[2]
    dry = "--dry-run" in sys.argv

    data = load(src)
    roots = data["roots"]
    bar = roots["bookmark_bar"]
    other = roots["other"]

    report = []

    # ---- 1. 移动散落书签 ----
    for url_frag, new_name, folder_path in MOVES:
        target = get_folder(bar, folder_path)
        while True:
            moved = None
            for c in other.get("children", []):
                if c.get("type") == "url" and url_frag in c.get("url", ""):
                    other["children"].remove(c)
                    c["name"] = new_name
                    target.setdefault("children", []).append(c)
                    moved = c
                    break
            if moved is None:
                break
            report.append(f"[移动] {moved['name']} → {folder_path[-1]}")

    # ---- 2. 全树 URL 去重（保留首次出现） ----
    seen = {}
    for root in [bar, other]:
        acc = []
        collect_url_nodes(root.get("children", []), acc)
        for parent_list, node in acc:
            url = node.get("url", "")
            if url in seen:
                parent_list.remove(node)
                report.append(f"[去重] 删除 {node['name']} (与「{seen[url]}」URL相同)")
            else:
                seen[url] = node["name"]

    # ---- 3. 输出 ----
    for line in report:
        print(line)
    print(f"\n共 {len(report)} 处变更")

    if not dry:
        if os.path.exists(dst):
            shutil.copy2(dst, dst + ".bak")
        save(dst, data)
        print(f"已写入: {dst}")
    else:
        print("(dry-run，未写入)")


if __name__ == "__main__":
    main()
