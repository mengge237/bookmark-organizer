# 收藏夹整理工具箱（bookmark-organizer）

把 Edge 收藏夹按管理学原则（MECE）整理成 9 个领域、最多 3 级的工具。已成功应用于真实 profile（329 条书签），并**通过官方 API 推上云端**（2026-08-21 验证：同步开启状态下重启不再回滚）。

## 目录结构

| 文件 | 作用 |
|---|---|
| `bookmark_tool.py` | 统一入口 CLI（status/backup/plan/apply/restore/push） |
| `reorg_plan.py` | 方案生成器：RULES 规则表 → 审核 markdown + 机器 JSON |
| `apply_plan.py` | 执行器：把方案 JSON 应用到 Bookmarks 文件（保留原书签元数据） |
| `ext/` | 临时 MV3 扩展（chrome.bookmarks 官方 API），`push` 命令用它把整理结果推上云端 |
| `收藏夹重组方案.md` | 最近一次整理方案的审核文档 |
| `reorg_plan.json` | 最近一次方案（机器可读，apply/push 的输入） |
| `backup/` | 自动/手动备份 |

## 使用方法

```bash
python bookmark_tool.py status              # 查看当前结构总览
python bookmark_tool.py backup              # 手动备份
python bookmark_tool.py plan                # 生成整理方案（审核 + 未匹配清单）
python bookmark_tool.py apply               # 应用方案（自动备份；须先关 Edge）
python bookmark_tool.py restore             # 从 backup/ 恢复最新备份
python bookmark_tool.py push                # 走官方 API 把方案推上云端（同步可保持开启）
# 所有命令支持 --file 指定 Bookmarks 路径（调试/测试用）
# push 附加参数: --wait-upload SEC(默认90) --no-relaunch(调试用) --edge-args "..." --force
```

日常维护流程：**新增了书签 → `plan` 看未匹配清单 → 在 `reorg_plan.py` 的 RULES 里加规则 → `push` → 重启验证无回滚**。

## 管理学方法论（本次整理采用的原则）

1. **MECE**：互斥穷尽——每个书签有且只有一个归类。
2. **统一分类维度**：顶层按「领域」划分（不用频率/活跃度等易变维度）。
3. **管理幅度 ≤7**：每个文件夹的直接子项控制在 7±2，超出则再分。
4. **层级 ≤3**：三级目录足够日常使用，更深即错误。
5. **不删只归**：疑似重复/失效的进「回收站」并注明理由，确认后才手动删除。
6. **改名修复**：空名/坏名书签改名（Pinterest、Pixiv、ArtStation）。
7. **任务场景优先**：找东西按「干什么事」定位——建模去建模美术，写码去开发工具。

## ⚠️ Edge 同步机制（血泪教训）

- Edge 151 启动后 ~2 秒会用**云端收藏夹合并本地文件**；**文件级修改永远不会上传到云端**。
- **唯一能把本地整理结果推进云端的路径**：官方 API（临时 MV3 扩展 `chrome.bookmarks` 的 create/move/update/removeTree）——改动被同步引擎当作正常用户操作上传。`push` 命令即走此路径，成功后云端即持有新结构，同步可保持开启。
- `push` 的内部流程：关 Edge → 备份 → 用 `--load-extension=ext` 启动 → 扩展加载 30s 后（等同步下载安定）应用方案 → 校验顶层结构完全一致 → `uninstallSelf()` 自卸载 → 等 90s 让同步上传 → 普通重启验证 60s 无回滚。
- 扩展的触发用「三保险」：`onInstalled` + `onStartup` + 模块求值兜底排期——因为 `--load-extension` 的扩展会在 profile 里留下注册记录，**第二次加载不再触发 onInstalled**（本次踩坑：真实 profile 第一次测试就注册了扩展，正式推送时 onInstalled 静默失效）。
- 扩展应用是**幂等**的：已在目标文件夹的书签跳过移动，重复运行几乎零改动（重试安全）。
- `--disable-sync` 启动参数可临时阻止同步（调试用），但该会话内改动不会上传。
- Edge 151 禁止在默认 user-data-dir 上开 `--remote-debugging-port`（CDP 只能连调试 profile：`--user-data-dir=C:\temp\edge-debug-profile`）。
- Bookmarks 数据在 `<user-data-dir>\Default\Bookmarks`（不是 user-data-dir 根目录）；手工编辑需删除 `checksum` 和 `sync_metadata`，Edge 启动会重建。
- 编辑文件前必须完全关闭 Edge（`Stop-Process -Name msedge -Force`），否则退出时被覆盖。
- 验证方法：`Default\favorites_diagnostic.log` 的 `BookmarksSnapshot Startup total=… bar=… other=…` 及是否有 `BookmarkNodeMoved` 回滚记录。
- 调试 profile 先干跑：`push --file "C:\temp\edge-debug-profile\Default\Bookmarks" --edge-args "--user-data-dir=C:\temp\edge-debug-profile --disable-sync --no-first-run" --no-relaunch`（先手动把真实 Bookmarks 复制进调试 profile 并去掉 checksum/sync_metadata）。
