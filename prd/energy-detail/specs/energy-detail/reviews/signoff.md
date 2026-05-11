# Round 6 · 签字 · 精力详情页 ｜ v0.5

> 各角色 owner 在自己的 checklist 上打勾。任何一项未勾，spec 不能进入 frozen 状态。

```yaml
prd_version: v0.5
frozen_at:
status_before: reviewing
status_after: frozen
```

> v0.5 较 v0.4 变更：补齐 §1/§2/§3/§4 叙事化、TL;DR 字段规范、AC related_decisions 显式注释、api.yaml 边界改写为用户感知措辞、HTML 重构为 screens.html 并 token 化。设计 / 前端 / 后端 / QA 需重新过一遍并签字。

## 产品 PM

- [x] 我已确认 TL;DR Card 的 intent / non_goals / risk
- [x] 我已确认所有 DEC 决议（DEC-01~05，见 `../adr/`）
- [x] Round 5 自审清单中接受的 13 条问题已全部修复（v0.1→v0.3）
- [x] metric 已明确跳过（PM 决定：基础功能页面不设独立指标，记入 deviations）

签字：PM 日期：2026-05-10

## 设计

- [ ] 我已确认 SCR-01（日视图）× 7 状态：正常 / 欠佳 / 无数据 / 加载骨架 / 缓存态 / 子维度缺失 / 无数据
- [ ] 我已确认 SCR-02（周视图）× 2 状态：正常 / Detail 失败降级
- [ ] 我已确认 SCR-03（月视图）：slot-based 柱状图，与现有二级页一致
- [ ] 评价 4 档颜色（完美绿/良好蓝/需注意橙/严重影响红）token 引用正确
- [ ] 缓存态横幅、骨架屏 shimmer、"数据积累中"文案确认

签字：____________ 日期：____________

## 前端

- [ ] 我已确认 api.yaml：`/api/energy/detail` + `/api/energy/trend` 两个接口
- [ ] 我已确认 events.yaml：4 个埋点事件（viewed / view_switched / date_changed / subdim_tapped）
- [ ] 前端直接使用 API 返回的 `energy_rating`，不自行计算阈值
- [ ] HealthDetailBasePage 可复用，无需重建页面框架
- [ ] 月视图柱状图复用现有 slot-based 方案
- [ ] 缓存层复用现有 health data 缓存，TTL 24h
- [ ] 刷新机制复用现有 HealthKit observer，前台切回时触发
- [ ] 下拉刷新（AC-14）、加载骨架（AC-13）、部分失败降级（AC-15）可交付

签字：____________ 日期：____________

## 后端

- [ ] 我已确认 api.yaml：EnergyDetail / EnergyTrend schema、SubDimension / RatingTier 枚举
- [ ] 错误码已完备：NO_DATA / FUTURE_DATE / RANGE_TOO_LARGE / UNAUTHORIZED / SERVER_ERROR / TIMEOUT
- [ ] sleep.score 范围 [0,100]、nap.score [0,30]、exercise.score [-20,20] 与现有服务一致
- [ ] 静息心率基线（14 天均值）+ 新用户无基线返回 null 已实现
- [ ] 数据隐私分级：低风险（无 PII）

签字：____________ 日期：____________

## 算法

> 不涉及。精力计算模型已在服务端运行，本需求不新增算法。

签字：N/A

## 测试 QA

- [ ] 15 条 AC 均可被测试覆盖（含 test_hint）
- [ ] AC-03 阈值边界值测试矩阵（5 子维度 × 最多 4 档）已识别
- [ ] AC-07 缺失组合矩阵（有睡眠无小睡/有小睡无睡眠/全无/周视图混合）已识别
- [ ] AC-13/14/15 降级路径需 mock 网络/接口场景
- [ ] 灰区：AC-11 前台刷新依赖 HealthKit observer 时序，需探索性测试

签字：____________ 日期：____________

## 硬件 / 固件

> 不涉及。

签字：N/A

---

## 关闭条件

- [ ] PM、设计、前端、后端、QA 五个角色已签字
- [ ] `status.yaml.state` 已切换为 `frozen`
- [ ] 已打 git tag `spec-frozen-energy-detail-v0.5`

完成后，spec 进入实现阶段。任何修改必须 bump 主版本号并重新走 Round 5。
