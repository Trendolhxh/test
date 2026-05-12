#!/usr/bin/env python3
"""
prd-workflow lint
按 mode 校验产物：
  - patch:    校验 patches/{slug}.md 单文件
  - standard: 校验 specs/{slug}/ 但跳过 ui/ HTML
  - full:     校验 specs/{slug}/ 完整规则（含 prd.md 叙事化、UI 平铺）

用法:
  python scripts/lint.py specs/heart-rate-alert/        # 自动从 status.yaml 读 mode
  python scripts/lint.py patches/button-radius.md       # patch 模式
  python scripts/lint.py specs/{slug}/ --round 3        # 只跑该轮规则

退出码: 0 通过 ｜ 1 fail ｜ 2 仅 warn（放行）
"""
from __future__ import annotations
import argparse, re, sys
from pathlib import Path

try:
    import yaml  # type: ignore
except ImportError:
    print("需要 PyYAML：pip install pyyaml"); sys.exit(2)

# ---------- 常量 ----------
ID_RE = re.compile(r"^[A-Z]+-\d+(\.[a-z_]+)?$")
# 颜色字面量：hex / rgba / hsl / 常见 named color
COLOR_LITERAL_RE = re.compile(
    r"#[0-9a-fA-F]{3,8}\b"
    r"|rgba?\s*\([^)]*\)"
    r"|hsla?\s*\([^)]*\)"
    r"|\b(?:red|blue|green|yellow|black|white|orange|purple|pink|gray|grey|cyan|magenta)\b"
)
DECISION_TAG_RE = re.compile(r"\[DECISION-NEEDED[^\]]*\]")
TLDR_BLOCK_RE = re.compile(r"#\s*TL;DR\s*\n+```ya?ml\n(.*?)```", re.S)
CN_RE = re.compile(r"[一-鿿]")
VAGUE_WORDS = ["差不多","较合理","尽量","可能","较快","稍后"]
SECTION_RE = lambda h: re.compile(rf"#\s*{re.escape(h)}\s*\n(.*?)(?=\n#\s|\Z)", re.S)

# 硬越界词（fail）—— 这些出现在 PRD/AC/contracts 里 100% 是越界
IMPL_HARD_PATTERNS = [
    (re.compile(r"\b(GET|POST|PUT|PATCH|DELETE)\s+/", re.I), "API 路径定义归研发"),
    (re.compile(r"openapi\s*:", re.I), "OpenAPI spec 归研发"),
    (re.compile(r"\brequest\s*[Bb]ody\b|response\s*[Bb]ody\b|response\s*[Ss]chema\b"), "request/response schema 归研发"),
    (re.compile(r"\bJSON\s*[Ss]chema\b"), "JSON Schema 归研发"),
    (re.compile(r"返回\s*\d{3}\b|HTTP\s*\d{3}|status\s*code", re.I), "HTTP 状态码归研发"),
    (re.compile(r"error[-_ ]?code\s*[:=]|错误码\s*[:：]?\s*[A-Z_]{3,}"), "错误码 ID 归研发（PM 只给用户看到的文案）"),
    (re.compile(r"\b(Redux|Zustand|MobX|Recoil|Pinia|Provider)\b"), "状态管理库是研发选型"),
    (re.compile(r"\b(useEffect|useState|useReducer|useMemo)\b"), "React hook 是研发选型"),
    (re.compile(r"memory_mb\s*:\s*[1-9]"), "内存数字是研发选型"),
    (re.compile(r"cpu_pct|cpu_percent|cpu_%"), "CPU 数字是研发选型"),
    (re.compile(r"schema\s*:\s*\n\s+type:\s*object", re.I), "数据 schema 定义归研发"),
]

# 软越界词（warn）—— 可能越界，提醒 PM 注意
IMPL_SOFT_PATTERNS = [
    (re.compile(r"复用[^。\n]{0,15}(observer|监听|订阅)", re.I), "复用 X observer/监听 是实现选型"),
    (re.compile(r"\bslot[-_ ]?based\b", re.I), "slot-based 是 UI 实现"),
    (re.compile(r"\bvirtual[- ]?scroll\b|虚拟滚动", re.I), "virtual scroll 是 UI 实现"),
    (re.compile(r"\blazy[- ]?load\b|懒加载", re.I), "lazy load 是 UI 实现"),
    (re.compile(r"local\s*DB\b|本地\s*DB|本地缓存层", re.I), "存储介质是研发选型"),
    (re.compile(r"TTL\s*[:=]?\s*\d+\s*(h|hr|hour|小时|min|秒|s)", re.I), "TTL 具体数字是研发选型（应给 staleness_tolerance）"),
    (re.compile(r"轮询|polling|WebSocket\s*推送|long\s*poll", re.I), "刷新机制选型归研发（应给 refresh_trigger 用户期望）"),
    (re.compile(r"\bSingleton\b|单例", re.I), "Singleton 是实现选型"),
    (re.compile(r"\bBLE\b|Bluetooth|I2C|SPI\b", re.I), "通信协议选型归硬件工程师"),
    (re.compile(r"paths:\s*\n\s+/", re.I), "API paths 结构归研发"),
]

def check_impl_smell(report: Report, text: str, where: str):
    """扫越界关键词：硬越界 fail，软越界 warn"""
    for pat, msg in IMPL_HARD_PATTERNS:
        m = pat.search(text)
        if m:
            report.fail(f"[boundary] {where} 出现研发实现细节 `{m.group(0)}`：{msg}")
    for pat, msg in IMPL_SOFT_PATTERNS:
        m = pat.search(text)
        if m:
            report.warn(f"[boundary] {where} 出现疑似实现选型词 `{m.group(0)}`：{msg}")

# ---------- 报告 ----------
class Report:
    def __init__(self):
        self.fails: list[str] = []; self.warns: list[str] = []
    def fail(self, m): self.fails.append(m)
    def warn(self, m): self.warns.append(m)
    def exit(self):
        for w in self.warns: print(f"WARN  {w}")
        for f in self.fails: print(f"FAIL  {f}")
        if self.fails: print(f"\n❌ {len(self.fails)} fail, {len(self.warns)} warn"); sys.exit(1)
        if self.warns: print(f"\n⚠️  {len(self.warns)} warn (放行)"); sys.exit(2)
        print("\n✅ all checks passed"); sys.exit(0)

def load_yaml(p: Path):
    if not p.exists(): return None
    try: return yaml.safe_load(p.read_text(encoding="utf-8"))
    except Exception as e: return {"_error": str(e)}

def cn_len(s: str) -> int:
    return len("".join(CN_RE.findall(s)))

# ============================================================
# Patch 模式
# ============================================================
def lint_patch(report: Report, path: Path):
    if not path.exists(): report.fail(f"找不到 {path}"); return
    text = path.read_text(encoding="utf-8")
    for r in ["## TL;DR","## Why","## Change","## Acceptance Criteria","## Test hint","## Affects"]:
        if r not in text: report.fail(f"[patch] 缺段落 `{r}`")
    m = re.search(r"## TL;DR\s*\n+(.+?)(?=\n##|\Z)", text, re.S)
    if m:
        n = cn_len(m.group(1))
        if n > 100: report.fail(f"[patch] TL;DR 中文 {n} 字 > 100")
        else: print(f"  TL;DR 中文 {n} 字 ✓")
    ac_lines = re.findall(r"^\s*-\s*AC-\d+", text, re.M)
    if not (1 <= len(ac_lines) <= 3): report.fail(f"[patch] AC 数量 {len(ac_lines)}，应 ∈ [1,3]")
    for v in VAGUE_WORDS:
        if v in text: report.fail(f"[patch] 含模糊词 `{v}`")
    if any(k in text for k in ["医疗","付款","合规"]):
        report.warn("[patch] 检测到合规/付款/医疗相关词，建议升级 standard")

# ============================================================
# Standard / Full 模式
# ============================================================
def parse_tldr(prd_path: Path):
    """返回 (tldr_dict, decisions_dict)。兼容旧/新 decisions_made 格式。"""
    if not prd_path.exists(): return None, {}
    text = prd_path.read_text(encoding="utf-8", errors="ignore")
    m = TLDR_BLOCK_RE.search(text)
    if not m: return None, {}
    try: data = yaml.safe_load(m.group(1)) or {}
    except Exception: return None, {}
    # decisions_made：兼容 dict（旧）和 list[{id, tag}]（新）
    dm = data.get("decisions_made") or []
    decs = {}
    if isinstance(dm, dict):
        for k, v in dm.items(): decs[k] = v
    elif isinstance(dm, list):
        for x in dm:
            if isinstance(x, dict) and x.get("id"): decs[x["id"]] = x.get("tag","")
    for d in (data.get("candidate_decisions") or []):
        if isinstance(d, dict) and d.get("id") and d["id"] not in decs: decs[d["id"]] = ""
    return data, decs

def check_prd_narrative(report: Report, prd_path: Path):
    """检查 prd.md 的叙事段、决议表、AC 概览、屏幕清单。返回 §4 SCR 列表"""
    if not prd_path.exists(): report.fail(f"[setup] 找不到 prd.md"); return []
    text = prd_path.read_text(encoding="utf-8")

    # TL;DR 字数
    m = TLDR_BLOCK_RE.search(text)
    if not m: report.fail("[round-1] 未找到 # TL;DR YAML 段"); return []
    tl_cn = cn_len(m.group(1))
    if tl_cn > 200: report.fail(f"[round-1] TL;DR 中文 {tl_cn} 字 > 200")
    else: print(f"  TL;DR 中文 {tl_cn} 字 ✓")

    # product_shape 必填
    try: tldr_data = yaml.safe_load(m.group(1)) or {}
    except Exception: tldr_data = {}
    if not (tldr_data.get("product_shape") or "").strip():
        report.fail("[round-1] TL;DR 缺 `product_shape`（形态锚点必填）")

    # §1 叙事段 ≥150 字
    s1 = SECTION_RE("1. 背景与用户故事").search(text) or SECTION_RE("1.背景与用户故事").search(text)
    if not s1: report.fail("[round-1] 缺 `# 1. 背景与用户故事` 段")
    else:
        body = s1.group(1).strip()
        n = cn_len(body)
        if n < 150:
            report.fail(f"[round-1] §1 叙事段 {n} 字 < 150；禁止只写'见 problem-card.md'")
        else:
            print(f"  §1 叙事 {n} 字 ✓")

    # §2 决议表必须有'决议'列且每条 ≥4 中文字
    s2 = SECTION_RE("2. 决策记录").search(text) or SECTION_RE("2.决策记录").search(text)
    if not s2: report.fail("[round-2] 缺 `# 2. 决策记录` 段")
    else:
        body = s2.group(1)
        if "决议" not in body:
            report.fail("[round-2] §2 决议表必须有'决议'列（一句话结论）")
        rows = re.findall(r"\|\s*(DEC-\d+)\s*\|([^\n]+)\|", body)
        for did, row_rest in rows:
            # row_rest 含中间列；测中文字数
            cn = cn_len(row_rest)
            if cn < 4:
                report.fail(f"[round-2] §2 决议表 {did} 的'决议'列过短（中文 {cn} 字），疑似纯链接")

    # §3 AC 概览 ≥30 字叙述
    s3 = SECTION_RE("3. AC 概览").search(text) or SECTION_RE("3. AC概览").search(text) \
         or SECTION_RE("3. AC 索引").search(text)
    if not s3:
        report.warn("[round-3] 缺 `# 3. AC 概览` 段")
    else:
        body = s3.group(1).strip()
        # 排除纯链接行
        narrative = "\n".join([ln for ln in body.split("\n")
                              if not ln.strip().startswith("[")
                              and not ln.strip().startswith("见")
                              and "见 [" not in ln])
        n = cn_len(narrative)
        if n < 30:
            report.fail(f"[round-3] §3 AC 概览叙述 {n} 字 < 30；禁止只写'见 acceptance-criteria.yaml'")

    # §4 屏幕清单表
    s4 = SECTION_RE("4. UI 屏幕清单").search(text) or SECTION_RE("4. UI规格").search(text) \
         or SECTION_RE("4. UI 规格").search(text)
    scr_list = []
    if not s4:
        report.warn("[round-3.5] 缺 `# 4. UI 屏幕清单` 段")
    else:
        body = s4.group(1)
        scr_list = re.findall(r"\|\s*(SCR-\d+)\s*\|", body)
        if not scr_list:
            report.fail("[round-3.5] §4 屏幕清单缺 SCR-XX 行")
        else:
            print(f"  §4 屏幕清单 {len(scr_list)} 屏 ✓")

    # prd.md 全文扫实现选型词（warn）
    check_impl_smell(report, text, "prd.md")

    return scr_list

def check_problem_card(report: Report, root: Path):
    p = root / "problem-card.md"
    if not p.exists(): report.warn("[round-0] 缺 problem-card.md"); return
    text = p.read_text(encoding="utf-8")
    # advance check 全勾
    if re.search(r"-\s*\[\s*\]\s*用户显式回复.*?进入 Round 1", text):
        report.fail("[round-0] problem-card.md '用户显式回复进入 Round 1' 未勾")

def check_deviations(report: Report, root: Path, tldr: dict):
    """status.yaml.deviations 非空时 prd.md TL;DR 须列出"""
    status = load_yaml(root / "status.yaml") or {}
    devs = status.get("deviations") or []
    tldr_devs = (tldr or {}).get("deviations")
    if devs and not tldr_devs:
        report.warn("[round-1] status.yaml 有 deviations，但 prd.md TL;DR 未列出 deviations")

def check_ac(report: Report, root: Path, decisions: dict):
    p = root / "acceptance-criteria.yaml"
    data = load_yaml(p)
    if not data: report.warn("[round-3] 缺 acceptance-criteria.yaml"); return {}
    if "_error" in data: report.fail(f"[round-3] yaml 解析失败：{data['_error']}"); return {}
    acs = data.get("acceptance_criteria", [])
    seen: set[str] = set()
    for ac in acs:
        i = ac.get("id","")
        if not i: report.fail("[round-3] AC 缺 id"); continue
        if not ID_RE.match(i): report.fail(f"[round-3] AC id 格式非法：{i}")
        if i in seen: report.fail(f"[round-3] AC id 重复：{i}")
        seen.add(i)
        for k in ("title","given","when","then","test_hint"):
            if not ac.get(k): report.fail(f"[round-3] {i} 缺字段 `{k}`")
        # 必须关联 ≥1 DEC（metric 可选）
        rds = ac.get("related_decisions")
        if rds is None:
            report.fail(f"[round-3] {i} 缺 related_decisions 字段")
        elif rds:
            for d in rds:
                if d not in decisions:
                    report.fail(f"[round-3] {i} 关联了未知的 {d}")
        # rds 为空列表是允许的（独立 AC），不再 fail
        # 模糊词
        text = " ".join([str(x) for x in (ac.get("then") or [])])
        for v in VAGUE_WORDS:
            if v in text: report.fail(f"[round-3] {i} then 含模糊词 `{v}`")
        # 实现选型词（warn）
        check_impl_smell(report, text, f"AC {i} then")
    # DEC 至少被 1 条 AC 引用（warn）
    ref = {d for ac in acs for d in (ac.get("related_decisions") or [])}
    for d in decisions:
        if d not in ref:
            report.warn(f"[round-3] {d} 未被任何 AC 引用")
    return {ac.get("id"): ac for ac in acs}

def check_ui_html(report: Report, root: Path, ac_index: dict, scr_list: list[str]):
    """full 模式：检查 ui/screens.html 平铺（或兼容 round-3.5*.html）"""
    ui = root / "ui"
    if not ui.exists():
        report.fail("[round-3.5] full 模式必须有 ui/ 目录与 screens.html"); return
    screens = ui / "screens.html"
    if not screens.exists():
        alt = list(ui.glob("round-3.5*.html"))
        if not alt:
            report.fail("[round-3.5] full 模式缺 ui/screens.html"); return
        if len(alt) > 1:
            report.warn(f"[round-3.5] ui/ 含 {len(alt)} 份 round-3.5*.html；推荐合并为单文件 screens.html 平铺")
        screens = alt[0]
    text = screens.read_text(encoding="utf-8", errors="ignore")
    # 颜色字面量：剥离 :root token 定义区
    style_match = re.search(r"<style[^>]*>(.*?)</style>", text, re.S)
    css = style_match.group(1) if style_match else ""
    css_outside_root = re.sub(r":root\s*\{[^}]*\}", "", css, flags=re.S)
    hits = COLOR_LITERAL_RE.findall(css_outside_root)
    hits = [h for h in hits if h.lower() not in ("none","transparent","currentcolor","inherit")]
    if hits:
        report.fail(f"[round-3.5] {screens.name} 在 :root 之外用了颜色字面量：{set(hits[:5])}")
    # 必须 ≥1 SCR、≥1 AC 引用
    ac_refs = set(re.findall(r"AC-\d+", text))
    if not ac_refs: report.fail(f"[round-3.5] {screens.name} 无任何 AC 引用")
    scr_refs = set(re.findall(r"SCR-\d+", text))
    if not scr_refs: report.fail(f"[round-3.5] {screens.name} 无任何 SCR 引用")
    # prd.md §4 与 HTML SCR 一致
    if scr_list:
        missing = set(scr_list) - scr_refs
        if missing:
            report.fail(f"[round-3.5] prd.md §4 列出但 HTML 中缺：{sorted(missing)}")
        extra = scr_refs - set(scr_list)
        if extra:
            report.warn(f"[round-3.5] HTML 含但 prd.md §4 未列出：{sorted(extra)}")
    # Round 1.5 草图必须粗糙
    for p in ui.glob("round-1.5-*.html"):
        t = p.read_text(encoding="utf-8", errors="ignore")
        if "var(--color-accent" in t or "tokens.json" in t:
            report.warn(f"[round-1.5] {p.name} 不应使用 design token，草图必须粗糙")

def check_ui_table(report: Report, prd_path: Path):
    """standard 模式：检查 prd.md §4 含屏幕清单"""
    # check_prd_narrative 已查过；此处保留为占位以保持调用对称性
    pass

def check_contracts(report: Report, root: Path, mode: str):
    cdir = root / "contracts"
    if not cdir.exists(): report.warn("[round-4] 没有 contracts/ 目录"); return
    # 扫所有 contract yaml 的越界词
    for yfile in cdir.glob("*.yaml"):
        text = yfile.read_text(encoding="utf-8", errors="ignore")
        check_impl_smell(report, text, f"contracts/{yfile.name}")
    # user_facing_errors 每条必须有 user_sees_zh
    de = load_yaml(cdir / "data-expectations.yaml")
    if de and isinstance(de, dict):
        for err in (de.get("user_facing_errors") or []):
            if not (err.get("user_sees_zh") or "").strip():
                report.fail(f"[round-4] data-expectations.yaml user_facing_errors 缺 user_sees_zh")
    # 算法不确定态检查（兼容新旧文件名）
    algo_file = cdir / "algorithm-boundary.yaml"
    if not algo_file.exists():
        algo_file = cdir / "algorithm.yaml"
    algo = load_yaml(algo_file)
    if algo and isinstance(algo, dict):
        node = algo.get("algorithm_boundary") or algo.get("algorithm") or algo
        if isinstance(node, dict):
            u = node.get("uncertain_states") or node.get("related_screens_for_uncertain_states") or {}
            for k in ("low_confidence","timeout","model_unavailable"):
                entry = u.get(k)
                if not entry:
                    report.fail(f"[round-4] {algo_file.name} 不确定态 `{k}` 未定义")
                elif isinstance(entry, dict) and not (entry.get("user_sees_zh") or entry.get(k) or "").strip():
                    report.fail(f"[round-4] {algo_file.name} 不确定态 `{k}` 缺 user_sees_zh")

def check_decision_resolved(report: Report, root: Path, state: str):
    if state != "frozen": return
    for p in root.rglob("*.md"):
        text = p.read_text(encoding="utf-8", errors="ignore")
        if DECISION_TAG_RE.search(text):
            report.fail(f"[round-2] frozen 仍有 [DECISION-NEEDED] @ {p.relative_to(root)}")

def check_status(report: Report, p: Path):
    s = load_yaml(p) or {}
    if not s: report.warn("[setup] 缺 status.yaml"); return None, "standard"
    state = s.get("state","drafting"); mode = s.get("mode","standard")
    if state not in ("drafting","reviewing","frozen"): report.fail(f"[setup] 非法 state `{state}`")
    if mode not in ("patch","standard","full"): report.fail(f"[setup] 非法 mode `{mode}`")
    return s, mode

# ============================================================
def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("path", help="specs/{slug}/ 或 patches/{slug}.md")
    ap.add_argument("--round", help="只跑指定轮次")
    args = ap.parse_args()

    p = Path(args.path); rep = Report()

    if p.is_file() and p.suffix == ".md":
        print(f"lint patch {p}"); lint_patch(rep, p); rep.exit()

    if not p.is_dir(): print(f"找不到 {p}"); sys.exit(2)

    print(f"lint {p}")
    status, mode = check_status(rep, p / "status.yaml")
    print(f"  mode = {mode}")

    state = (status or {}).get("state","drafting")
    prd = p / "prd.md"
    tldr_data, decisions = parse_tldr(prd)

    if not args.round or args.round in ("0","all"):
        check_problem_card(rep, p)

    scr_list = []
    if not args.round or args.round in ("1","2","3","3.5","all"):
        scr_list = check_prd_narrative(rep, prd) or []

    if not args.round or args.round in ("1","all"):
        check_deviations(rep, p, tldr_data or {})

    if not args.round or args.round in ("2","all"):
        adir = p / "adr"
        adr_ids = {x.stem.replace("ADR-","DEC-") for x in adir.glob("ADR-*.md")} if adir.exists() else set()
        if state in ("reviewing","frozen"):
            for d in decisions:
                if d not in adr_ids: rep.fail(f"[round-2] {d} 缺对应 ADR")

    ac_idx = {}
    if not args.round or args.round in ("3","all"):
        ac_idx = check_ac(rep, p, decisions)

    if not args.round or args.round in ("3.5","all"):
        if mode == "full": check_ui_html(rep, p, ac_idx, scr_list)
        elif mode == "standard": check_ui_table(rep, prd)

    if not args.round or args.round in ("4","all"):
        check_contracts(rep, p, mode)

    if not args.round or args.round in ("5","all"):
        check_decision_resolved(rep, p, state)

    rep.exit()

if __name__ == "__main__": main()
