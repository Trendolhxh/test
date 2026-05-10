#!/usr/bin/env python3
"""
prd-workflow lint
按 mode 校验产物：
  - patch:    校验 patches/{slug}.md 单文件
  - standard: 校验 specs/{slug}/ 但跳过 ui/ HTML
  - full:     校验 specs/{slug}/ 完整规则

用法:
  python scripts/lint.py specs/heart-rate-alert/        # 自动从 status.yaml 读 mode
  python scripts/lint.py patches/button-radius.md       # patch 模式（直接传文件路径）
  python scripts/lint.py specs/{slug}/ --round 3        # 只跑该轮规则

退出码:
  0 通过 ｜ 1 fail ｜ 2 仅 warn（放行）
"""
from __future__ import annotations
import argparse, re, sys
from pathlib import Path

try:
    import yaml  # type: ignore
except ImportError:
    print("需要 PyYAML：pip install pyyaml")
    sys.exit(2)

# ---------- 常量 ----------
ID_RE = re.compile(r"^[A-Z]+-\d+(\.[a-z_]+)?$")
HEX_RE = re.compile(r"#[0-9a-fA-F]{3,8}\b")
DECISION_TAG_RE = re.compile(r"\[DECISION-NEEDED[^\]]*\]")
TLDR_BLOCK_RE = re.compile(r"#\s*TL;DR\s*\n+```ya?ml\n(.*?)```", re.S)
CN_RE = re.compile(r"[一-鿿]")
VAGUE_WORDS = ["差不多","较合理","尽量","可能","较快","稍后"]

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

# ============================================================
# Patch 模式
# ============================================================
def lint_patch(report: Report, path: Path):
    if not path.exists():
        report.fail(f"找不到 {path}"); return
    text = path.read_text(encoding="utf-8")
    # 必填字段
    required = ["## TL;DR", "## Why", "## Change", "## Acceptance Criteria", "## Test hint", "## Affects"]
    for r in required:
        if r not in text:
            report.fail(f"[patch] 缺段落 `{r}`")
    # TL;DR ≤ 100 中文字
    m = re.search(r"## TL;DR\s*\n+(.+?)(?=\n##|\Z)", text, re.S)
    if m:
        cn = "".join(CN_RE.findall(m.group(1)))
        if len(cn) > 100:
            report.fail(f"[patch] TL;DR 中文 {len(cn)} 字 > 100")
        else:
            print(f"  TL;DR 中文 {len(cn)} 字 ✓")
    # AC 数量 ∈ [1, 3]
    ac_lines = re.findall(r"^\s*-\s*AC-\d+", text, re.M)
    if not (1 <= len(ac_lines) <= 3):
        report.fail(f"[patch] AC 数量 {len(ac_lines)}，应在 [1, 3]")
    # 模糊词
    for v in VAGUE_WORDS:
        if v in text:
            report.fail(f"[patch] 含模糊词 `{v}`，请量化")
    # 升级触发关键字（warn 即可，不强制）
    if any(k in text.lower() for k in ["医疗","付款","合规","payment","medical","compliance"]):
        report.warn("[patch] 检测到合规/付款/医疗相关词，建议升级到 standard")

# ============================================================
# Standard / Full 模式：现有规则
# ============================================================
def extract_metrics_decisions(prd_path: Path):
    if not prd_path.exists(): return [], {}
    text = prd_path.read_text(encoding="utf-8", errors="ignore")
    m = TLDR_BLOCK_RE.search(text)
    if not m: return [], {}
    try: data = yaml.safe_load(m.group(1)) or {}
    except Exception: return [], {}
    metrics = [x.get("name") for x in (data.get("metrics") or []) if x.get("name")]
    decs = {}
    for d in (data.get("candidate_decisions") or []):
        if d.get("id"): decs[d["id"]] = d
    for k, v in (data.get("decisions_made") or {}).items(): decs[k] = v
    return metrics, decs

def check_tldr_length(report: Report, prd_path: Path):
    if not prd_path.exists():
        report.fail(f"[setup] 找不到 {prd_path}"); return
    text = prd_path.read_text(encoding="utf-8")
    m = TLDR_BLOCK_RE.search(text)
    if not m: report.fail("[round-1] prd.md 中未找到 # TL;DR YAML 段"); return
    cn = "".join(CN_RE.findall(m.group(1)))
    if len(cn) > 200: report.fail(f"[round-1] TL;DR 中文 {len(cn)} 字 > 200")
    else: print(f"  TL;DR 中文 {len(cn)} 字 ✓")

def check_ac(report: Report, root: Path, decisions: dict, metrics: list[str]):
    p = root / "acceptance-criteria.yaml"
    data = load_yaml(p)
    if not data:
        report.warn(f"[round-3] 缺 acceptance-criteria.yaml"); return {}
    if "_error" in data:
        report.fail(f"[round-3] yaml 解析失败：{data['_error']}"); return {}
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
        related = (ac.get("related_metrics") or []) + (ac.get("related_decisions") or [])
        if not related: report.fail(f"[round-3] {i} 未关联任何 metric 或 DEC")
        for d in (ac.get("related_decisions") or []):
            if d not in decisions: report.fail(f"[round-3] {i} 关联了未知的 {d}")
        for m in (ac.get("related_metrics") or []):
            if m not in metrics: report.warn(f"[round-3] {i} 关联了未声明的 metric `{m}`")
        text = " ".join([str(x) for x in (ac.get("then") or [])])
        for v in VAGUE_WORDS:
            if v in text: report.fail(f"[round-3] {i} then 含模糊词 `{v}`")
    cov = {m for ac in acs for m in (ac.get("related_metrics") or [])}
    for m in metrics:
        if m not in cov: report.warn(f"[round-3] metric `{m}` 未被任何 AC 覆盖")
    ref = {d for ac in acs for d in (ac.get("related_decisions") or [])}
    for d in decisions:
        if d not in ref: report.warn(f"[round-3] {d} 未被任何 AC 引用")
    return {ac.get("id"): ac for ac in acs}

def check_ui_html(report: Report, root: Path, ac_index: dict):
    """仅 full 模式调用"""
    ui = root / "ui"
    if not ui.exists():
        report.fail("[round-3.5] full 模式必须有 ui/ 目录与 HTML"); return
    html_files = list(ui.glob("round-3.5-*.html"))
    if not html_files:
        report.fail("[round-3.5] full 模式缺 round-3.5-*.html"); return
    for p in html_files:
        text = p.read_text(encoding="utf-8", errors="ignore")
        body = text.split(":root", 1)[-1] if ":root" in text else text
        body = body.split("</style>", 1)[-1]
        if HEX_RE.search(body):
            report.fail(f"[round-3.5] {p.name} 在 design token 之外用了 hex")
        ac_refs = re.findall(r"AC-\d+(?:-[a-z]+)?", text)
        if not ac_refs: report.fail(f"[round-3.5] {p.name} 没有任何 AC 引用")
        for a in set(ac_refs):
            base = a.split("-followup")[0]
            if ac_index and base not in ac_index:
                report.warn(f"[round-3.5] {p.name} 引用了未知 AC {a}")
    for p in ui.glob("round-1.5-*.html"):
        text = p.read_text(encoding="utf-8", errors="ignore")
        if "var(--color-accent" in text or "tokens.json" in text:
            report.warn(f"[round-1.5] {p.name} 不应使用 design token，草图必须粗糙")

def check_ui_table(report: Report, prd_path: Path, ac_index: dict):
    """standard 模式调用：检查 prd.md 含 ui 表格段"""
    if not prd_path.exists(): return
    text = prd_path.read_text(encoding="utf-8")
    if "ui:" not in text and "UI 规格" not in text:
        report.warn("[round-3.5] standard 模式建议在 prd.md 含 `ui:` 屏幕表格")
    # 简单引用检查
    ac_refs = re.findall(r"AC-\d+", text)
    for a in set(ac_refs):
        if ac_index and a not in ac_index:
            report.warn(f"[round-3.5] prd.md 引用了未知 AC {a}")

def check_contracts(report: Report, root: Path, mode: str):
    cdir = root / "contracts"
    if not cdir.exists():
        report.warn("[round-4] 没有 contracts/ 目录"); return
    if mode == "full":
        algo = load_yaml(cdir / "algorithm.yaml")
        if algo and isinstance(algo, dict):
            node = algo.get("algorithm", algo)
            if isinstance(node, dict):
                u = node.get("related_screens_for_uncertain_states") or {}
                for k in ("low_confidence","timeout","model_unavailable"):
                    if not u.get(k): report.fail(f"[round-4] algorithm.yaml 不确定态 `{k}` 未关联 UI 状态")

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
# 入口
# ============================================================
def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("path", help="specs/{slug}/ 或 patches/{slug}.md")
    ap.add_argument("--round", help="只跑指定轮次")
    args = ap.parse_args()

    p = Path(args.path)
    rep = Report()

    # patch 模式：直接传文件路径
    if p.is_file() and p.suffix == ".md":
        print(f"lint patch {p}")
        lint_patch(rep, p); rep.exit()

    if not p.is_dir():
        print(f"找不到 {p}"); sys.exit(2)

    print(f"lint {p}")
    status, mode = check_status(rep, p / "status.yaml")
    print(f"  mode = {mode}")

    state = (status or {}).get("state","drafting")
    prd = p / "prd.md"
    metrics, decisions = extract_metrics_decisions(prd)

    if not args.round or args.round in ("1","all"):
        check_tldr_length(rep, prd)

    if not args.round or args.round in ("2","all"):
        adir = p / "adr"
        adr_ids = {x.stem.replace("ADR-","DEC-") for x in adir.glob("ADR-*.md")} if adir.exists() else set()
        if state in ("reviewing","frozen"):
            for d in decisions:
                if d not in adr_ids: rep.fail(f"[round-2] {d} 缺对应 ADR")

    ac_idx = {}
    if not args.round or args.round in ("3","all"):
        ac_idx = check_ac(rep, p, decisions, metrics)

    if not args.round or args.round in ("3.5","all"):
        if mode == "full": check_ui_html(rep, p, ac_idx)
        elif mode == "standard": check_ui_table(rep, prd, ac_idx)

    if not args.round or args.round in ("4","all"):
        check_contracts(rep, p, mode)

    if not args.round or args.round in ("5","all"):
        check_decision_resolved(rep, p, state)

    rep.exit()

if __name__ == "__main__": main()
