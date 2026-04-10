# 数据同步状态 测试用例

> 用于测试首页数据同步状态的 UI 表现和诊断逻辑。输入为设备状态和 HealthKit 返回条件，预期输出为 UI 行为。
> 研发基于描述构建 mock 的 HealthKit 响应和设备状态。

---

## A. 同步成功场景

### A01 正常早晨同步 · 全部数据更新

**输入条件**：
- 早上 8:00 打开 App，距上次同步 > 5 分钟
- Apple Watch 已配对、蓝牙已开、可达
- HealthKit 返回昨夜睡眠数据（7h）、静息心率（62bpm）、活动消耗（320kcal）
- 所有数据与上次缓存不同

**预期行为**：
- 打开后立即：3 个小卡片 + 功能卡片展示 shimmer 动画
- HealthKit 返回后（<3s）：shimmer 淡出 → 数值 CountUp 动画（旧值→新值，0.5s）
- 同步状态条：不显示
- Smart Digest：收到 `data_refreshed (has_new_data=true)`，检查触发条件
- 缓存更新：所有卡片的 `last_sync_success` 和 `last_value` 写入新值

### A02 中午重新打开 · 无新数据

**输入条件**：
- 中午 12:30 打开 App，距上次同步 2 小时
- HealthKit 返回数据与缓存完全一致

**预期行为**：
- 打开后：shimmer 短暂播放
- HealthKit 返回后：shimmer 消失，静态展示当前值（无 CountUp 动画）
- 同步状态条：不显示
- Smart Digest：收到 `data_refreshed (has_new_data=false)`，展示缓存

### A03 部分数据更新 · 心率更新但睡眠不变

**输入条件**：
- 下午 15:00 打开 App
- HealthKit 返回：心率有新数据（resting_bpm 从 65→62），睡眠和活动数据无变化

**预期行为**：
- 心率卡片：shimmer → CountUp 动画（65→62）
- 睡眠/消耗卡片：shimmer → 静态展示（无动画过渡）
- Smart Digest：可能触发（如果心率变化超过阈值 Δ≥3bpm）

### A04 快速切换前后台 · 5 分钟内

**输入条件**：
- 用户 3 分钟前刚同步成功，切后台后再次回到前台

**预期行为**：
- 不触发新的 HealthKit 查询（防抖：<5 分钟）
- 直接展示上次同步结果，无 shimmer 动画
- Smart Digest：维持当前展示，不触发

### A05 后台已同步 · HealthKit 极速返回

**输入条件**：
- Apple Health 在 App 后台期间已完成数据同步
- app_open 时 HealthKit 查询立即返回新数据（<0.5s）

**预期行为**：
- shimmer 极短（<0.5s）后立即过渡到 CountUp 动画
- 用户几乎无感知加载过程，直接看到数值更新

---

## B. Apple Watch 同步失败场景

### B01 HealthKit 未授权

**输入条件**：
- 用户首次打开 App 但拒绝了 HealthKit 授权
- `HKHealthStore.authorizationStatus` 返回 `.sharingDenied`

**预期行为**：
- 数据卡片：全部显示 "--"（无缓存值）
- 同步状态条：显示"需要健康数据权限，点击前往设置"
- 点击状态条：跳转 iOS 系统设置页
- Smart Digest：不展示（新用户无数据）

### B02 Apple Watch 未配对

**输入条件**：
- `WCSession.default.isPaired == false`
- HealthKit 中无历史数据，primary_source 未设置

**预期行为**：
- 数据卡片：全部显示 "--"
- 同步状态条：显示"未检测到 Apple Watch"
- Smart Digest：不展示

### B03 iPhone 蓝牙已关闭

**输入条件**：
- `CBCentralManager.state == .poweredOff`
- `WCSession.isPaired == true`
- 有上次缓存数据（睡眠 92，心率 87，消耗 672）

**预期行为**：
- 数据卡片：显示缓存值（92 / 87 / 672）+ 灰色"08:15 更新"
- 数值透明度降至 60%
- 同步状态条：显示"iPhone 蓝牙已关闭，开启后将自动同步"
- Smart Digest：展示缓存的摘要

### B04 Apple Watch 不可达（锁定/充电/超距）

**输入条件**：
- `WCSession.isPaired == true`
- `CBCentralManager.state == .poweredOn`
- `WCSession.isReachable == false`
- 有缓存数据

**预期行为**：
- 数据卡片：显示缓存值 + 灰色更新时间
- 同步状态条：显示"手表暂时无法连接，请确认已解锁并在身边"
- **不**显示"手表锁定中"或"手表充电中"（无法区分具体原因）
- Smart Digest：展示缓存

### B05 同步超时（10 秒无响应）

**输入条件**：
- Apple Watch 已配对、蓝牙已开、显示可达
- HealthKit 查询发出后 10 秒无返回

**预期行为**：
- 0-10s：shimmer 动画持续播放
- 10s 后：shimmer 消失 → 显示缓存值 + 同步状态条"数据同步中，稍后将自动更新"
- 下次 app_open 自动重试

### B06 部分超时 · 睡眠超时但心率成功

**输入条件**：
- HealthKit 心率查询 2s 内返回新数据
- HealthKit 睡眠查询 10s 超时

**预期行为**：
- 心率卡片：2s 时 shimmer → CountUp 动画，正常展示
- 睡眠卡片：10s 时 shimmer → 缓存值 + 灰色更新时间
- 同步状态条：显示（因为有卡片处于 stale）
- `data_refreshed`：仍然发送（因为心率有新数据）

---

## C. 第三方设备场景

### C01 小米手环 · 数据正常同步

**输入条件**：
- primary_source: `com.xiaomi.mihealthapp`（小米运动）
- HealthKit 中最新 sample 来自小米运动，时间为 30 分钟前
- 查询返回新数据

**预期行为**：
- 与 Apple Watch 同步成功表现一致：shimmer → CountUp
- 不走 WCSession 诊断分支（WCSession 仅用于 Apple Watch）

### C02 小米手环 · 数据过期（伴侣 App 未同步）

**输入条件**：
- primary_source: `com.xiaomi.mihealthapp`
- HealthKit 中最新 sample 时间为 3 小时前（超过 2h 阈值）
- HealthKit 查询成功但无新数据

**预期行为**：
- 数据卡片：显示缓存值 + 灰色"05:30 更新"
- 同步状态条：显示"数据未更新，请打开小米运动同步"
- **不**显示 Apple Watch 相关的诊断信息（蓝牙/配对等）

### C03 佳明手表 · 数据过期

**输入条件**：
- primary_source: `com.garmin.connect.mobile`（Garmin Connect）
- HealthKit 中最新 sample 时间为 5 小时前

**预期行为**：
- 数据卡片：显示缓存值 + 灰色"03:15 更新"
- 同步状态条：显示"数据未更新，请打开 Garmin Connect 同步"
- 伴侣 App 名称通过 primary_source 映射得到

### C04 用户更换设备 · 从 Apple Watch 换到小米手环

**输入条件**：
- 原 primary_source: `com.apple.health`（Apple Watch）
- 新数据来自 `com.xiaomi.mihealthapp`
- WCSession.isPaired == false（Apple Watch 已取消配对）

**预期行为**：
- HealthKit 返回来自小米运动的新数据 → 正常 CountUp 展示
- primary_source 自动更新为 `com.xiaomi.mihealthapp`
- 后续 stale 时走第三方设备诊断分支

### C05 设备来源未知 · 新用户首次使用

**输入条件**：
- HealthKit 无历史数据，primary_source 未设置
- WCSession.isPaired == false（未配对 Apple Watch）

**预期行为**：
- 数据卡片：全部显示 "--"
- 同步状态条：显示"暂无数据，连接穿戴设备后可查看"
- 不假设用户使用哪种设备

---

## D. 与 Smart Digest 共存场景

### D01 同步成功 + Smart Digest 触发新生成

**输入条件**：
- 同步成功，有新数据
- 距上次 Smart Digest 生成 > 15 分钟（冷却期已过）
- 新数据与快照的 diff 超过阈值

**预期行为**：
- 数据卡片：CountUp 动画展示新值
- Smart Digest：先展示缓存 → `data_refreshed` 后触发 LLM 生成 → 新摘要替换缓存
- 两个区域的更新独立进行，互不阻塞

### D02 同步失败 + Smart Digest 展示缓存

**输入条件**：
- 同步失败（Apple Watch 不可达）
- 有上次成功的 Smart Digest 缓存

**预期行为**：
- 数据卡片：显示缓存值 + stale 标记
- 同步状态条：显示原因
- Smart Digest：正常展示上次缓存的摘要和快捷提问（`data_refreshed` 未发送，走缓存逻辑）
- **Smart Digest 缓存摘要仍对用户有参考价值**，不因同步失败而隐藏

### D03 同步成功但无新数据 + Smart Digest 冷却期内

**输入条件**：
- 同步成功，数据与缓存一致（success_no_change）
- 距上次 Smart Digest 生成 < 15 分钟

**预期行为**：
- 数据卡片：静态展示（无动画）
- Smart Digest：展示缓存（冷却期内不重新生成）
- 两者都展示缓存内容，页面平稳无变化

### D04 部分同步成功 + Smart Digest 部分触发

**输入条件**：
- 心率同步成功（有新数据，Δ resting_bpm = -5）
- 睡眠同步失败（stale）
- Smart Digest 冷却期已过

**预期行为**：
- 心率卡片：CountUp 动画
- 睡眠卡片：缓存值 + stale 标记
- `data_refreshed` 发送（因为心率有新数据）
- Smart Digest：触发生成，但输入数据中睡眠部分为上次缓存值（非实时值），LLM 基于可用数据生成摘要

---

## E. 边界情况

### E01 新用户 · 无穿戴设备

**输入条件**：
- HealthKit 已授权
- 无任何历史数据，WCSession 未配对
- 无 primary_source

**预期行为**：
- 问候语：正常展示
- 数据卡片：全部 "--"
- 同步状态条："暂无数据，连接穿戴设备后可查看"
- Smart Digest：不展示
- 快捷提问：不展示

### E02 连续下拉刷新 · 防抖

**输入条件**：
- 用户在 10 秒内连续下拉 3 次

**预期行为**：
- 第 1 次下拉：正常触发同步，shimmer 动画
- 第 2、3 次下拉（10s 内）：忽略，不重新触发
- UI 无异常跳动

### E03 同步中点击卡片进入详情

**输入条件**：
- 睡眠卡片正在 shimmer 动画中
- 用户点击睡眠卡片进入详情页

**预期行为**：
- 导航不被阻塞，正常跳转到详情页
- 详情页使用缓存数据展示
- 后台同步继续进行，返回首页后展示最新状态

### E04 数据超过 24 小时

**输入条件**：
- HealthKit 查询成功，但最新 sample 的 endDate 是昨天 22:00（>24h 前）
- 用户整天未佩戴设备

**预期行为**：
- 数据卡片：显示昨天的缓存值 + 灰色"昨天 22:00"
- 视为 stale（即使 HealthKit 查询本身成功，数据新鲜度不达标）
- 同步状态条：基于 primary_source 类型显示对应文案

### E05 HealthKit 数据库不可用

**输入条件**：
- HealthKit 查询返回 `HKError.errorDatabaseInaccessible`

**预期行为**：
- 所有卡片 → stale
- 同步状态条：显示兜底文案"数据同步中，稍后将自动更新"
- 不暴露技术错误码给用户

### E06 网络恢复自动重试

**输入条件**：
- 当前 stale 状态（之前因网络问题同步失败）
- NWPathMonitor 检测到网络从不可用变为可用

**预期行为**：
- stale 卡片自动进入 syncing 状态（shimmer 动画）
- 无需用户操作
- 如果重试成功 → CountUp 动画 + 状态条消失
- 如果重试仍失败 → 保持 stale，不反复弹状态条动画

### E07 多数据来源并存

**输入条件**：
- Apple Watch 写入了睡眠数据
- iPhone 自带传感器写入了步数数据
- 小米手环也写入了心率数据

**预期行为**：
- primary_source 以最近一次写入的来源为准
- 各卡片的数据取 HealthKit 中最新的 sample，不区分来源
- stale 诊断文案基于 primary_source 展示

### E08 首次安装 · 弹出 HealthKit 授权

**输入条件**：
- 用户首次打开 App
- 系统弹出 HealthKit 授权对话框
- 用户尚未选择允许或拒绝

**预期行为**：
- 数据卡片：shimmer 动画（等待授权结果）
- 用户授权后 → 立即发起 HealthKit 查询
- 用户拒绝后 → stale + "需要健康数据权限，点击前往设置"
