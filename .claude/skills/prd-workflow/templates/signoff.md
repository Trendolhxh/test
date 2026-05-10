<!--
Round 6 · 终审签字
位置：specs/{slug}/reviews/signoff.md
完成后：
  1. status.yaml.state 改为 frozen
  2. git tag spec-frozen-{slug}-v{version}
  3. prd.md 顶部注入 frozen_at
-->

# Round 6 · 签字 · {{中文功能名}} ｜ v{{version}}

> 各角色 owner 在自己的 checklist 上打勾。任何一项未勾，spec 不能进入 frozen 状态。

```yaml
prd_version: v0.1
frozen_at:                              # 全员签字后由脚本注入
status_before: reviewing
status_after: frozen
```

## 产品 PM

- [ ] 我已确认 TL;DR Card 的 intent / non_goals / risk / metrics
- [ ] 我已确认所有 DEC 决议（见 `../adr/`）
- [ ] 我已确认 AC 与 metric 一一对应
- [ ] Round 5 自审清单中接受的问题已全部修复

签字：____________ 日期：____________

## 设计

- [ ] 我已确认所有 SCR × state 的 UI 规格 HTML
- [ ] 所有文案、动效、token 引用正确
- [ ] 算法不确定态已有 UI 兜底

签字：____________ 日期：____________

## 前端

- [ ] 我已确认 api.yaml 与 events.yaml
- [ ] 现有组件足够覆盖 UI 规格，无需重新创建
- [ ] 性能预算（首屏、动效 FPS、电量）我能交付

签字：____________ 日期：____________

## 后端

- [ ] 我已确认 api.yaml 的端点 / schema / 错误码 enum
- [ ] 数据隐私分级合规
- [ ] 现有服务能覆盖；如需新建/迁移已写入 ADR

签字：____________ 日期：____________

## 算法

- [ ] 我已确认 algorithm.yaml 的 IO schema 与 SLA
- [ ] 评估指标与切片表现可达
- [ ] 失败语义（low_confidence / timeout / model_unavailable）已有 UI 状态对应

签字：____________ 日期：____________

## 测试 QA

- [ ] 我已确认每条 AC 都可被测试覆盖
- [ ] AC ↔ Test 双向引用 traceability 已建立
- [ ] 灰区清单（自动化覆盖不到、需要探索性测试）已识别

签字：____________ 日期：____________

## 硬件 / 固件（如涉及）

- [ ] 我已确认 hardware.yaml 中 ICD diff 兼容
- [ ] 功耗预算 / 时序 / 信号完整性满足
- [ ] HIL 自动化能复现 AC 中相关条目

签字：____________ 日期：____________

---

## 关闭条件

- [ ] 所有适用角色已签字
- [ ] `status.yaml.state` 已切换为 `frozen`
- [ ] 已打 git tag `spec-frozen-{{slug}}-v{{version}}`

完成后，spec 进入实现阶段。任何修改必须 bump 主版本号并重新走 Round 5。
