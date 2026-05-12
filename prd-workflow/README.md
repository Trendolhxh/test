# prd-workflow

把"AI 一次写完 8000 字 PRD，人读不动"切成 8 轮渐进协作。中文写人能读的，英文写机器能 grep 的。

## 安装

复制 `prd-workflow/` 到下面任一位置：

```
~/.claude/skills/prd-workflow/                  # 个人
{your-repo}/.claude/skills/prd-workflow/        # 团队共享
```

## 触发

直接说"我们要做一个 X 功能，写 PRD"。AI 会从 Round 0 开始，每轮 5–10 分钟。

## 跑 lint

```bash
pip install pyyaml
python scripts/lint.py specs/{slug}/
```

退出码 0 通过，1 fail（不许进下一轮），2 仅 warn。

## 文件清单

- `SKILL.md` — 完整流程定义、advance condition、HTML 结构描述（这是主入口）
- `templates/` — 7 个 schema 模板（Round 0–6）
- `scripts/lint.py` — 9 条硬约束的校验脚本
- `example/heart-rate-alert/` — 可参考的最小完整示例

详细工作流和约束见 [SKILL.md](./SKILL.md)。
