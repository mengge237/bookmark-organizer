// Bookmark Reorg Pusher v2 —— 通过官方 chrome.bookmarks API 操作收藏夹
// 改动会被同步引擎当作正常用户操作上传云端。
// 三种可选输入（全部缺失 = 空操作）:
//   plan.json   重组方案: 移动/改名/建文件夹
//   add.json    推荐网站模式 ON: 创建书签（URL 已存在则跳过）
//   remove.json 推荐网站模式 OFF: 删除书签（guid 优先、URL 兜底，只删计划内的）
// 流程: 加载后 30s（等同步下载安定）→ 执行 → 顶层结构精确校验 → 成功自卸载 / 失败重试(最多3次)
const BAR_ID = '1';
const OTHER_ID = '2';

const norm = (u) => (u || '').trim().replace(/\/+$/, '').toLowerCase();

async function loadJson(name) {
  try {
    const res = await fetch(chrome.runtime.getURL(name));
    if (!res.ok) return [];
    return await res.json();
  } catch (e) { return []; }
}
const loadPlan = () => loadJson('plan.json');
const loadAdd = () => loadJson('add.json');
const loadRemove = () => loadJson('remove.json');

function rootsOf(tree) {
  const bar = tree[0].children.find(c => c.id === BAR_ID) || tree[0].children[0];
  const other = tree[0].children.find(c => c.id === OTHER_ID);
  return { bar, other };
}

// 全树索引（运行前快照）:
//   urlIdx:  url -> [id]（遍历序，支持同 URL 重复项）
//   nodeInfo: id -> {parentId, title}
//   urlMap:  url -> [{id, top, inBar}]
//   guidMap: guid -> {id, top, inBar}
function indexTree(tree) {
  const urlIdx = {};
  const nodeInfo = {};
  const urlMap = {};
  const guidMap = {};
  const walk = (nodes, parentId, top, inBar) => {
    for (const n of nodes) {
      nodeInfo[n.id] = { parentId, title: n.title };
      if (n.url) {
        const u = norm(n.url);
        (urlIdx[u] = urlIdx[u] || []).push(n.id);
        const rec = { id: n.id, top, inBar, url: u };
        (urlMap[u] = urlMap[u] || []).push(rec);
        if (n.guid) guidMap[n.guid] = { id: n.id, top, inBar };
      } else if (n.children) {
        walk(n.children, n.id, inBar ? (top || n.title) : top, inBar);
      }
    }
  };
  for (const root of tree[0].children) {
    walk(root.children || [], root.id, null, root.id === BAR_ID);
  }
  return { urlIdx, nodeInfo, urlMap, guidMap };
}

function targetPathsOf(entries) {
  const s = new Set();
  for (const e of entries) {
    let p = '';
    for (const seg of e.folders || []) { p = p ? p + '/' + seg : seg; s.add(p); }
  }
  return s;
}

// 建立 路径 -> folder id（仅书签栏内、路径相对书签栏）
function indexFolders(barChildren) {
  const map = new Map();
  const walk = (nodes, path) => {
    for (const n of nodes) {
      if (!n.url) {
        const p = path ? path + '/' + n.title : n.title;
        map.set(p, n.id);
        if (n.children) walk(n.children, p);
      }
    }
  };
  walk(barChildren, '');
  return map;
}

// 自顶向下创建缺失的目标文件夹（复用同名空壳）
async function ensureFolders(targetPaths, folders, barId) {
  const byDepth = [...targetPaths].sort((a, b) => a.split('/').length - b.split('/').length);
  for (const p of byDepth) {
    if (folders.has(p)) continue;
    const i = p.lastIndexOf('/');
    const parentPath = i === -1 ? '' : p.slice(0, i);
    const title = i === -1 ? p : p.slice(i + 1);
    const parentId = parentPath === '' ? barId : folders.get(parentPath);
    if (!parentId) continue;
    const created = await chrome.bookmarks.create({ parentId, title });
    folders.set(p, created.id);
  }
}

// 应用重组方案：移动 + 改名（已在目标文件夹的跳过，幂等）
async function applyPlan(plan, folders, urlIdx, nodeInfo) {
  const counters = {};
  let moved = 0, skipped = 0, renamed = 0, errors = 0;
  const moveErrors = [];
  for (const e of plan) {
    const k = counters[e.url] || 0;
    counters[e.url] = k + 1;
    const id = (urlIdx[e.url] || [])[k];
    if (!id) { errors++; continue; }
    const parentId = folders.get((e.folders || []).join('/'));
    if (!parentId) { errors++; continue; }
    try {
      if (e.rename && nodeInfo[id] && nodeInfo[id].title !== e.rename) {
        await chrome.bookmarks.update(id, { title: e.rename });
        renamed++;
      }
      if (nodeInfo[id] && nodeInfo[id].parentId === parentId) { skipped++; continue; }
      await chrome.bookmarks.move(id, { parentId });
      if (nodeInfo[id]) nodeInfo[id].parentId = parentId;
      moved++;
    } catch (err) {
      errors++;
      moveErrors.push({ name: e.name, url: e.url, error: String(err && err.message || err) });
    }
  }
  return { moved, skipped, renamed, errors, moveErrors };
}

// 推荐网站 ON：创建新书签（URL 已存在则跳过）
async function addSites(adds, folders, addPaths, urlSet, barId) {
  await ensureFolders(addPaths, folders, barId);
  const pending = [];
  for (const a of adds) {
    if (!urlSet.has(norm(a.url))) pending.push(a);
  }
  const created = [];
  for (const a of pending) {
    const parentId = folders.get((a.folders || []).join('/'));
    if (!parentId) continue;
    try {
      const node = await chrome.bookmarks.create({ parentId, title: a.name, url: a.url });
      created.push({ url: a.url, id: node.id });
    } catch (e) {}
  }
  return { pending, created };
}

// 推荐网站 OFF：删除书签（guid 优先、URL 兜底且只取书签栏内的首个匹配）
async function removeSites(removes, urlMap, guidMap) {
  const removed = [];
  for (const r of removes) {
    let node = null;
    if (r.guid && guidMap[r.guid]) node = guidMap[r.guid];
    if (!node) {
      const list = urlMap[norm(r.url)] || [];
      node = list.find(x => x.inBar) || list[0] || null;
    }
    if (!node) continue;
    try {
      await chrome.bookmarks.remove(node.id);
      removed.push({ id: node.id, top: node.top, url: node.url || norm(r.url) });
    } catch (e) {}
  }
  return removed;
}

// 清理变空的旧文件夹（反复扫描；路径相对各自根；避开目标路径）
async function cleanupPass(targetPaths) {
  const collectEmpty = (tree) => {
    const toRemove = [];
    const walk = (nodes, path, depth) => {
      for (const n of nodes) {
        if (!n.url && n.children !== undefined) {
          const p = path ? path + '/' + n.title : n.title;
          walk(n.children, p, depth + 1);
          if (n.children.length === 0 && !targetPaths.has(p)) {
            toRemove.push({ id: n.id, title: n.title, depth });
          }
        }
      }
    };
    for (const root of tree[0].children) {
      if (root.children) walk(root.children, '', 0);
    }
    toRemove.sort((a, b) => b.depth - a.depth);
    return toRemove;
  };

  let removedFolders = 0;
  const removeErrors = [];
  for (let pass = 0; pass < 3; pass++) {
    const fresh = await chrome.bookmarks.getTree();
    const toRemove = collectEmpty(fresh);
    if (toRemove.length === 0) break;
    for (const x of toRemove) {
      try { await chrome.bookmarks.removeTree(x.id); removedFolders++; }
      catch (err) { removeErrors.push({ title: x.title, error: String(err && err.message || err) }); }
    }
  }
  return { removedFolders, removeErrors };
}

// 期望顶层结构：方案 + 实际新增 − 实际删除。
// 扣减规则与 python 侧 expected_structure 一致：被删书签只有在方案中有对应条目、
// 且删掉后方案覆盖不足时才扣减（deficit = max(0, 方案数 − (文件数 − 删除数))）。
// 推荐书签不在方案里 → deficit 为 0 → 不扣减，删完正好回到方案结构。
function expectedCounts(plan, pending, removed, urlMap) {
  const expected = {};
  const planCounts = {};
  for (const e of plan) {
    expected[e.folders[0]] = (expected[e.folders[0]] || 0) + 1;
    const u = norm(e.url);
    planCounts[u] = (planCounts[u] || 0) + 1;
  }
  for (const a of pending) expected[a.folders[0]] = (expected[a.folders[0]] || 0) + 1;
  if (!removed.length) return expected;
  const fileCounts = {};
  for (const u in urlMap) fileCounts[u] = urlMap[u].length;
  const removedCounts = {};
  for (const x of removed) removedCounts[x.url] = (removedCounts[x.url] || 0) + 1;
  const deficit = {};
  for (const u in removedCounts) {
    deficit[u] = Math.max(0, (planCounts[u] || 0) - ((fileCounts[u] || 0) - removedCounts[u]));
  }
  for (const x of removed) {
    if (x.top && deficit[x.url] > 0) {
      deficit[x.url]--;
      expected[x.top] = (expected[x.top] || 0) - 1;
      if (expected[x.top] <= 0) delete expected[x.top];
    }
  }
  return expected;
}

async function verify(expected) {
  const tree = await chrome.bookmarks.getTree();
  const { bar, other } = rootsOf(tree);
  if (other && other.children && other.children.length > 0) return false;
  const countUrls = (n) => {
    let c = 0;
    for (const ch of n.children || []) c += ch.url ? 1 : countUrls(ch);
    return c;
  };
  const actual = {};
  for (const n of bar.children || []) {
    if (n.url) { actual[''] = (actual[''] || 0) + 1; continue; }
    actual[n.title] = countUrls(n);
  }
  if ((actual[''] || 0) !== 0) return false;
  for (const [k, v] of Object.entries(expected)) {
    if (actual[k] !== v) return false;
    delete actual[k];
  }
  return Object.keys(actual).length === 0;
}

async function run(attempt) {
  let expected = null;
  let error = null;
  try {
    const plan = await loadPlan();
    const adds = await loadAdd();
    const removes = await loadRemove();

    const tree0 = await chrome.bookmarks.getTree();
    const { bar } = rootsOf(tree0);
    const idx = indexTree(tree0);
    const folders = indexFolders(bar.children);
    const planPaths = targetPathsOf(plan);
    const addPaths = targetPathsOf(adds);

    await ensureFolders(planPaths, folders, bar.id);
    const moveStats = await applyPlan(plan, folders, idx.urlIdx, idx.nodeInfo);
    const addStats = await addSites(adds, folders, addPaths, new Set(Object.keys(idx.urlIdx)), bar.id);
    const removed = await removeSites(removes, idx.urlMap, idx.guidMap);
    const cleanStats = await cleanupPass(new Set([...planPaths, ...addPaths]));

    expected = expectedCounts(plan, addStats.pending, removed, idx.urlMap);
    await chrome.storage.local.set({
      moved: moveStats.moved, skipped: moveStats.skipped, renamed: moveStats.renamed,
      errors: moveStats.errors, created: addStats.created.length,
      removed: removed.length, removedFolders: cleanStats.removedFolders,
      moveErrors: moveStats.moveErrors, removeErrors: cleanStats.removeErrors,
    });
  } catch (err) {
    error = String(err && err.message || err);
    await chrome.storage.local.set({ error });
  }

  const ok = error === null && expected !== null && await verify(expected);
  if (ok) {
    await chrome.storage.local.set({ success: true, attempts: attempt });
    if (chrome.management && chrome.management.uninstallSelf) {
      try { await chrome.management.uninstallSelf(); } catch (e) {}
    }
  } else if (attempt < 3) {
    await chrome.storage.local.set({ success: false, attempts: attempt, error });
    chrome.alarms.create('retry' + attempt, { when: Date.now() + 60000 });
  } else {
    await chrome.storage.local.set({ success: false, attempts: attempt, gaveUp: true, error });
  }
}

function schedule() {
  // 30s 后开工：让启动期同步下载/合并安定
  chrome.alarms.create('start', { when: Date.now() + 30000 });
}

chrome.runtime.onInstalled.addListener(schedule);
chrome.runtime.onStartup.addListener(schedule);
schedule(); // 模块求值兜底：--load-extension 场景下 SW 被拉起即排期

// 必须把 run() 的 Promise 返回给监听器，MV3 service worker 才会在
// 异步执行期间保持存活（否则中途被回收，改动只做了一半）。
chrome.alarms.onAlarm.addListener((a) => {
  if (a.name === 'start') return run(1);
  if (a.name.startsWith('retry')) return run(parseInt(a.name.slice(5), 10) + 1);
});
