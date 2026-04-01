# Skill: 反馈卡片回复处理

> 触发条件：用户提交了行为反馈卡片（feedback-submit 场景），`completion_value` 为 `done` / `partial` / `not_done`

## 输入变量

由 scene directive `feedback-submit.md` 注入：

| 变量 | 说明 |
|------|------|
| `${suggestion_description}` | 当初给的行动建议内容 |
| `${completion_value}` | `done` / `partial` / `not_done` |
| `${follow_up_text}` | 用户附加的文字说明（可能为 `"none"`） |

---

## 完整流程

### Step 1 — 读取结果并记录

无论结果如何，**第一步都是** `save_memory`：

```
save_memory(
  category: "intervention_feedback",
  content: "手机放客厅干预：用户反馈 done/partial/not_done，附加说明：XXX"
)
```

保持用户原话中的关键词，不加模型推断。`save_memory` 静默执行，**绝不说"我记录了"**。

---

### Step 2 — 按结果分支处理

#### 分支 A：`done`（完成了）

1. **具体肯定，关联数据**
   - 如果有当天睡眠数据，调用 `get_health_data(metrics: ["sleep_stages", "hrv_sdnn"], range: "today")` 看看执行日的数据表现
   - 把行动和数据变化关联起来："手机放客厅那晚，入睡时间比前天早了 20 分钟"
   - **禁止**空洞表扬（"做得好""继续保持"）——必须有具体数据或行为细节

2. **考虑下一步**
   - 已执行 3 天以上 → 考虑巩固习惯或适当提升难度
   - 首次执行 → 肯定 + 提一句"明天继续试试？"
   - 用 `suggest_replies` 引导："继续这个方案 / 想试试进阶 / 先就这样"

#### 分支 B：`partial`（部分完成）

1. **先肯定做到的部分**
   - "手机拿到客厅了但后来又拿回来了——至少迈出了第一步"
   - 部分完成 > 完全没做，这就是进步

2. **识别卡住的环节**
   - 如果 `follow_up_text` 有说明，据此理解障碍
   - 如果没有说明，用 `suggest_replies` 温和追问："是忘了还是中途觉得不方便？/ 不想聊这个"

3. **考虑降低门槛**
   - 原方案难度可能偏高 → 提议降低（"要不先试试只在周末放客厅？"）
   - 调用 `get_strategy(aspects: ["active"])` 确认当前干预状态再调整

#### 分支 C：`not_done`（没做）

1. **理解，不责备**
   - 绝不说"可惜""下次加油"——这是说教
   - 先表达理解："没做到很正常，我们看看是什么挡住了"

2. **了解障碍**
   - 如果 `follow_up_text` 已说明原因 → 直接回应
   - 如果没有 → 温和询问，用 `suggest_replies` 提供常见原因选项：
     ```
     suggest_replies([
       "工作太晚了没顾上",
       "试了但觉得不太对",
       "忘了",
       "不想聊这个"
     ])
     ```

3. **调整方案**
   - 调用 `get_strategy(aspects: ["active", "history"])` 看这个干预的整体执行情况
   - 如果连续 2 次未执行 → 方案本身可能不合适，考虑换方向（不是用户的错）
   - 如果是偶发未执行 → 维持方案，调整执行条件（时间/难度）

---

### Step 3 — 闭环

- `done` → 如果决定继续当前方案，酌情发新的 `send_feedback_card` 跟踪下一次
- `partial` / `not_done` → 如果调整了方案，用新方案走 `skill-give-intervention-advice` 的闭环流程（提醒 + 反馈卡）
- 不管哪个分支，都不要在一次对话里追问太多——反馈处理完毕后给用户空间

---

## 禁止事项

- ❌ 空洞表扬（"做得好""加油"）
- ❌ 责备或暗示失望（"可惜""希望下次能做到"）
- ❌ 未执行就连续追问原因——提供选项让用户自主回应
- ❌ 说"我记录了你的反馈"——`save_memory` 静默执行
- ❌ 不看策略上下文就调整方案
