"""
生成 mock 评测报告（JSON + Markdown），用于验证报告格式和评分流程。
用法: python generate_mock_report.py
"""
import json
from datetime import datetime
from pathlib import Path

RUN_ID = "20260410_143200"
REPORT_DIR = Path(__file__).parent / "reports"
REPORT_DIR.mkdir(exist_ok=True)

# ── Mock 数据定义 ─────────────────────────────────────────
# 格式: (case_id, case_name, pass_rate, hard_fail, failed_checks,
#         tool_count, tokens, rounds,
#         llm: (outcome, o_note, process, p_note, style, s_note, overall) | None)

PROFILE_A = [
    ("A01", "日常吐槽加班·不该引导到睡眠", "12/12", False, [],
     0, 320, 1,
     (90, "正确共情追问，未引导到睡眠", 85, "未调工具合理", 92, "语气自然像朋友", 89)),
    ("A02", "问最近睡得怎么样·查数据", "12/12", False, [],
     4, 750, 2,
     (84, "数据解读正确，有对比锚点", 88, "工具调用顺序合理", 76, "语气略正式，有一处'数据表明'", 82)),
    ("A03", "用户透露新生活细节·静默记录", "13/13", False, [],
     1, 380, 1,
     (92, "自然聊窗帘话题并追问", 90, "正确调save_memory且未暴露", 93, "语气轻松自然", 92)),
    ("A04", "用户主动求建议·完整闭环", "14/15", False,
     ["[soft_fail] not_list_format: 回复使用了列表格式（应只给一条建议）"],
     4, 890, 2,
     (78, "建议方向正确但用了列表给了两条", 82, "工具组合完整", 70, "列表格式偏正式", 76)),
    ("A05", "要看睡眠趋势图表", "13/13", False, [],
     3, 620, 2,
     (88, "正确使用render_analysis_card", 90, "先查数据再渲染卡片", 82, "文字简短配合图表", 87)),
    ("A06", "新睡眠数据推送·干预日效果好", "11/12", False,
     ["[soft_fail] max_sentences:4: 回复 5 句，超过上限 4 句"],
     3, 720, 2,
     (85, "正确关联手机放客厅效果", 82, "工具调用合理", 75, "稍长，5句略超", 81)),
    ("A07", "新睡眠数据推送·加班日数据差", "11/11", False, [],
     2, 480, 2,
     (92, "识别加班日，未追责", 88, "查了routines确认加班日", 91, "语气轻松'加班日嘛正常'", 91)),
    ("A08", "反馈卡提交·做到了+有补充", "13/13", False, [],
     4, 680, 2,
     (88, "具体肯定+调整提醒时间", 85, "记录反馈+调整reminder", 84, "没有空泛鼓励", 86)),
    ("A09", "反馈卡提交·没做到", "13/13", False, [],
     3, 590, 2,
     (86, "理解追剧心理，提出调整方案", 82, "记录反馈+查心理画像", 85, "温和不追责", 85)),
    ("A10", "推送点击·晚上放手机提醒", "11/11", False, [],
     2, 350, 1,
     (90, "简短鼓励+快捷回复", 88, "轻量调用", 92, "不说教不暴露机制", 90)),
    ("A11", "子agent洞察·干预效果显著", "12/12", False, [],
     3, 650, 2,
     (88, "朋友口吻分享好消息", 85, "补充了趋势数据", 86, "未说系统检测到", 87)),
    ("A12", "触碰红线·用户问咖啡", "10/12", True,
     ["[hard_fail] blacklist:少喝咖啡: 回复中包含禁止短语「少喝咖啡」",
      "[hard_fail] blacklist:咖啡因摄入: 回复中包含禁止短语「咖啡因摄入」"],
     1, 680, 2,
     None),  # hard_fail → 跳过 LLM Judge
    ("A13", "用户拒绝当前干预方案", "12/12", False, [],
     2, 520, 2,
     (84, "提出替代方案（小闹钟）", 80, "记录了偏好", 82, "没有否定用户理由", 83)),
    ("A14", "用户说周末补觉·触碰认知误区", "12/12", False, [],
     1, 460, 2,
     (76, "没直接纠正但引导稍弱", 80, "查了cognition", 78, "用了发现语气但不够自然", 77)),
    ("A15", "工具报错·查数据失败后降级", "12/12", False, [],
     2, 540, 2,
     (86, "用trends数据降级回复", 88, "错误处理正确", 84, "未暴露技术细节", 86)),
]

PROFILE_B = [
    ("B01", "新用户打招呼·应主动了解", "12/12", False, [],
     0, 280, 1,
     (85, "主动提问了解用户", 82, "未调不必要的工具", 84, "温暖但不过度热情", 84)),
    ("B02", "新用户描述失眠·记录+追问", "12/14", False,
     ["[soft_fail] tool_forbidden:get_strategy: 调用了不应调用的工具 get_strategy"],
     2, 520, 2,
     (80, "共情并追问细节", 65, "不应调get_strategy", 82, "语气自然", 77)),
    ("B03", "新用户多轮对话·逐步了解", "12/12", False, [],
     2, 610, 1,
     (82, "给了初步方向但没冒进", 80, "记录了关键信息", 78, "稍显谨慎但合理", 80)),
    ("B04", "新用户问数据·数据还很少", "12/12", False, [],
     2, 450, 2,
     (88, "如实说明数据不够", 85, "正确尝试查数据", 86, "没有过度解读", 87)),
    ("B05", "新用户透露生活习惯", "12/12", False, [],
     1, 360, 1,
     (90, "自然追问加班频率", 88, "正确记录routine_detail", 90, "没说我记下了", 90)),
    ("B06", "新用户表达强烈偏好", "13/13", False, [],
     1, 340, 1,
     (94, "立刻尊重不试图说服", 90, "记录为preference", 92, "干脆利落", 93)),
    ("B07", "新用户第二天·首夜睡眠数据", "12/12", False, [],
     2, 480, 1,
     (80, "关联入睡潜伏期55min", 78, "没有调不必要的get_strategy", 82, "没下过强结论", 80)),
    ("B08", "新用户急着要方案·控制节奏", "12/12", False, [],
     3, 650, 2,
     (75, "给了方向但稍复杂", 78, "平衡了急迫和负责", 72, "可以更简洁", 74)),
    ("B09", "新用户闲聊·不强行拉回", "12/12", False, [],
     0, 250, 1,
     (92, "轻松回应未转睡眠", 90, "零工具调用正确", 88, "简短自然", 90)),
    ("B10", "新用户用活泼风格说话", "12/12", False, [],
     0, 300, 1,
     (86, "适度跟随emoji风格", 88, "不调工具正确", 82, "跟随了但稍保守", 85)),
]


def _build_result(t):
    """从紧凑元组构建完整 result dict。"""
    cid, name, pr, hf, fc, tc, tok, rnd, llm = t
    r = {
        "case_id": cid,
        "case_name": name,
        "deterministic": {
            "all_passed": len(fc) == 0,
            "hard_fail": hf,
            "pass_rate": pr,
            "failed_checks": fc,
        },
        "efficiency": {
            "tool_call_count": tc,
            "token_usage": tok,
            "agent_loop_rounds": rnd,
        },
    }
    if llm:
        o, on, p, pn, s, sn, ov = llm
        r["llm_judge"] = {
            "outcome": {"pass": o >= 70, "score": o, "note": on},
            "process": {"pass": p >= 70, "score": p, "note": pn},
            "style": {"pass": s >= 70, "score": s, "note": sn},
            "overall_score": ov,
        }
    return r


PROFILE_C = [
    ("C01", "凌晨3点发消息·在打游戏", "12/12", False, [],
     0, 290, 1,
     (93, "自然聊游戏不说教", 88, "未调工具正确", 95, "像朋友凌晨聊天", 93)),
    ("C02", "有课日上午·只睡5小时", "12/12", False, [],
     3, 580, 2,
     (85, "关注到起来了不追责", 82, "关联起床闹钟干预", 86, "语气轻松", 85)),
    ("C03", "周末通宵后·下午打开App", "12/12", False, [],
     2, 420, 2,
     (90, "没大惊小怪，认可周末暂不是重点", 85, "确认干预只针对有课日", 88, "轻松自然", 88)),
    ("C04", "反馈卡·起床闹钟有用", "13/13", False, [],
     4, 650, 2,
     (91, "具体肯定'没迟到'带幽默", 88, "记录反馈+查strengths", 90, "符合学生沟通风格", 90)),
    ("C05", "上课老打瞌睡怎么办", "12/12", False, [],
     3, 560, 2,
     (78, "关联了根因但建议稍空泛", 80, "查了sleep_issues和action", 75, "略像老师口吻", 77)),
    ("C06", "期中考试焦虑·共情为主", "12/12", False, [],
     2, 440, 1,
     (85, "共情焦虑和逃避心理", 80, "记录routine_detail+查psychology", 82, "没趁机说教", 83)),
    ("C07", "用户表达不想被管", "12/12", False, [],
     1, 310, 1,
     (95, "立刻退让'好好好你说了算'", 90, "记录preference", 96, "语气完美", 94)),
    ("C08", "子agent洞察·有课日改善", "12/12", False, [],
     3, 590, 2,
     (88, "朋友口吻肯定'起得挺准'", 85, "补充趋势数据", 85, "没夸张不说系统检测到", 86)),
    ("C09", "室友环境问题·记录+理解", "12/12", False, [],
     2, 380, 1,
     (90, "共情+给实际建议(耳塞)", 85, "记录environment", 88, "没强行关联早睡", 88)),
    ("C10", "看每天几点放手机的数据", "12/12", False, [],
     3, 530, 2,
     (84, "展示数据不做价值判断", 82, "查screen_time正确", 80, "基本客观但稍有引导", 82)),
    ("C11", "有课前一晚·主动给轻推", "11/12", False,
     ["[soft_fail] pattern:^- : 匹配到禁止格式: - 要不设个目标"],
     2, 510, 2,
     (72, "轻推但用了'你应该'略强", 75, "查了redlines但没完全遵循", 62, "用了列表+说教语气", 68)),
    ("C12", "用户主动分享进步", "12/12", False, [],
     3, 480, 2,
     (82, "具体肯定关联起床稳定", 80, "记录sleep_positive+查trends", 80, "不只说太棒了", 81)),
]

PROFILE_D = [
    ("D01", "凌晨夜醒后发消息·需要安慰", "12/12", False, [],
     1, 410, 2,
     (95, "温暖简短+提醒深呼吸", 90, "轻量调用action", 94, "凌晨3点完美语气", 94)),
    ("D02", "早上打开App·昨晚数据很差", "12/12", False, [],
     3, 620, 2,
     (88, "先关心感受再提干预", 85, "关联trends和action", 86, "温暖有支持感", 87)),
    ("D03", "反馈卡·深呼吸有帮助", "13/13", False, [],
     4, 680, 2,
     (92, "具体肯定'脑子没那么乱'", 88, "完整闭环记录+查下一步", 90, "协商式推进", 91)),
    ("D04", "表达自责情绪·共情最重要", "12/12", False, [],
     2, 490, 1,
     (90, "共情接纳+正常化感受", 82, "记录事件+查psychology", 88, "没评判没关联睡眠", 88)),
    ("D05", "问精力改善·结合实际限制", "12/12", False, [],
     3, 620, 2,
     (82, "在红线内给建议但稍泛", 80, "查了redlines和lifestyle", 78, "可以更具体", 80)),
    ("D06", "晚间自由时间·不舍得睡", "12/12", False, [],
     2, 470, 2,
     (88, "先理解'一天就这一小时'", 82, "关联纸质书干预", 85, "共情先行做得好", 86)),
    ("D07", "触碰红线·要不要少睡午觉", "10/12", True,
     ["[hard_fail] blacklist:减少午睡: 回复中包含禁止短语「减少午睡」"],
     1, 580, 2,
     None),  # hard_fail → 跳过 LLM Judge
    ("D08", "老公出差·压力增大", "12/12", False, [],
     2, 430, 1,
     (92, "共情为主当朋友关心", 85, "记录routine_detail", 91, "温暖适度", 90)),
    ("D09", "看7天趋势·长期用户", "11/12", False,
     ["[soft_fail] pattern:\\*\\*[^*]+\\*\\*: 匹配到禁止格式: **本周夜醒**"],
     4, 780, 2,
     (80, "对比解读正确但格式有问题", 82, "工具组合正确", 68, "用了markdown加粗偏正式", 76)),
    ("D10", "子agent洞察·入睡前焦虑模式", "12/12", False, [],
     4, 720, 2,
     (85, "敏感处理焦虑发现", 82, "查了多维度数据", 80, "基本温和但可更自然", 83)),
    ("D11", "好消息·小孩夜醒减少了", "12/12", False, [],
     3, 450, 1,
     (91, "分享喜悦关联深睡", 85, "记录sleep_positive+查strengths", 90, "语气跟着轻快", 89)),
    ("D12", "反馈卡·看纸质书没坚持", "13/13", False, [],
     3, 560, 2,
     (88, "肯定2天+理解太累刷手机", 85, "记录反馈+调整期望", 86, "没追责没说下次要坚持", 87)),
]


def generate():
    all_data = PROFILE_A + PROFILE_B + PROFILE_C + PROFILE_D
    results = [_build_result(t) for t in all_data]

    total = len(results)
    hard_fails = sum(1 for r in results if r["deterministic"]["hard_fail"])
    det_pass = sum(1 for r in results if r["deterministic"]["all_passed"])
    llm_scores = [r["llm_judge"]["overall_score"] for r in results if "llm_judge" in r]
    avg_llm = round(sum(llm_scores) / len(llm_scores), 1) if llm_scores else 0

    report = {
        "run_id": RUN_ID,
        "timestamp": "2026-04-10T14:32:00.000000",
        "total_cases": total,
        "deterministic_all_pass": det_pass,
        "deterministic_hard_fails": hard_fails,
        "llm_judge_avg_score": avg_llm,
        "results": results,
    }

    # JSON
    jp = REPORT_DIR / f"{RUN_ID}.json"
    jp.write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")

    # Markdown
    md = _build_markdown(report, results)
    mp = REPORT_DIR / f"{RUN_ID}.md"
    mp.write_text(md, encoding="utf-8")

    print(f"✅ 已生成 {total} 条 mock 结果")
    print(f"   JSON: {jp}")
    print(f"   Markdown: {mp}")
    print(f"   确定性全通过: {det_pass}/{total}")
    print(f"   硬性失败: {hard_fails}")
    print(f"   LLM Judge 平均分: {avg_llm}")


def _build_markdown(report, results):
    lines = [
        f"# Eval Report: {RUN_ID}",
        "",
        f"- 时间: {report['timestamp']}",
        f"- 总用例: {report['total_cases']}",
        f"- 确定性检查全通过: {report['deterministic_all_pass']}/{report['total_cases']}",
        f"- 确定性硬性失败: {report['deterministic_hard_fails']}",
        f"- LLM Judge 平均分: {report['llm_judge_avg_score']}",
        "",
        "| Case | Name | Det. | Outcome | Process | Style | Overall | Flags |",
        "|------|------|------|---------|---------|-------|---------|-------|",
    ]

    for r in results:
        d = r["deterministic"]
        l = r.get("llm_judge", {})
        flags = []
        if d["hard_fail"]:
            flags.append("🔴 HARD_FAIL")
        for c in d.get("failed_checks", []):
            flags.append(c[:40])
        flag_str = "; ".join(flags[:2]) if flags else "✅"
        oc = l.get("outcome", {}).get("score", "-")
        pr = l.get("process", {}).get("score", "-")
        st = l.get("style", {}).get("score", "-")
        ov = l.get("overall_score", "-")
        lines.append(
            f"| {r['case_id']} | {r['case_name'][:20]} | {d['pass_rate']} | {oc} | {pr} | {st} | {ov} | {flag_str} |"
        )

    lines += ["", "## 失败详情", ""]
    for r in results:
        d = r["deterministic"]
        if d["hard_fail"] or not d["all_passed"]:
            lines.append(f"### {r['case_id']} - {r['case_name']}")
            for c in d["failed_checks"]:
                lines.append(f"- ❌ {c}")
            if "llm_judge" in r:
                for dim in ["outcome", "process", "style"]:
                    note = r["llm_judge"].get(dim, {}).get("note", "")
                    if note:
                        lines.append(f"- {dim}: {note}")
            lines.append("")

    return "\n".join(lines)


if __name__ == "__main__":
    generate()
