# 用户速览模板

> 注入位置：system prompt，紧跟身份层之后
> 来源：用户上下文文档的 `[summary]` section，由子 agent 维护
> 预估 token：~80 tk

## 正常用户模板

```text
## 用户速览
{age}岁{gender}/{occupation}/{chronotype}/{living_situation} | 核心问题:{core_issue_chain} | 阶段:{intervention_stage} | 红线:{redlines} | 沟通:{communication_style}
```

### 示例

```text
## 用户速览
30岁男/产品经理/晚型人/独居 | 核心问题:睡前手机→上床晚→时长不足 | 阶段:干预中期,手机放客厅试跑有效 | 红线:咖啡,早起运动 | 沟通:数据驱动,不喜鸡汤,偶尔自嘲
```

## 新用户模板（记忆为空时注入）

```text
## 用户速览
暂无数据。这是新用户，请通过对话了解用户的基本情况、作息习惯和睡眠困扰。多提问、多记录（save_memory），不要急于给建议。
```
