// ══════════════════════════════════════
// MOCK DATA — all scene definitions
// ══════════════════════════════════════

const SCENES = {

  morning: {
    isNight: false,
    greeting: '早上好',
    statusTime: '9:41',
    metric: { value: '7.5', unit: 'h', deltaClass: 'positive', deltaText: '↑ +0.3h vs 昨天', label: '今日预估高能时长' },
    windows: ['09:30–11:45', '18:45–21:10'],
    digest: '昨晚深睡 22% 回到健康区间，HRV 也涨了 3ms——今天上午是你的主场',
    questions: ['深睡为什么会波动', '怎么保持这状态', '高能时段怎么用'],
    attrs: [
      { icon: '🌙', name: '昨夜睡眠时长', value: '7h12m', contrib: '+0.2h', cls: 'positive' },
      { icon: '💤', name: '深睡占比', value: '22%（↑3%）', contrib: '+0.1h', cls: 'positive' },
      { icon: '🏃', name: '昨日运动', value: '跑步 30min', contrib: '+0.2h', cls: 'positive' },
      { icon: '⏰', name: '入睡偏差', value: '比推荐晚 15min', contrib: '-0.2h', cls: 'negative' },
    ],
    notables: [],
    desc: '晨起场景：用户起床后打开 App，查看今日高能时长预估和行动建议。',
  },

  morning_up: {
    isNight: false,
    greeting: '早上好',
    statusTime: '9:41',
    metric: { value: '9.2', unit: 'h', deltaClass: 'positive', deltaText: '↑ +1.8h vs 昨天', label: '今日预估高能时长' },
    windows: ['08:30–13:00', '16:00–20:30'],
    digest: '深睡 28%，近 30 天最佳记录——今天的你状态炸裂，把最重要的事都搬过来',
    questions: ['为什么今天这么好', '这状态能持续吗', '今天适合做什么'],
    attrs: [
      { icon: '💤', name: '深睡占比', value: '28%（↑9%）', contrib: '+0.8h', cls: 'positive' },
      { icon: '❤️', name: 'HRV', value: '58ms（↑13ms）', contrib: '+0.6h', cls: 'positive' },
      { icon: '🌙', name: '昨夜睡眠时长', value: '8h30m', contrib: '+0.4h', cls: 'positive' },
    ],
    notables: [
      { type: 'positive', badge: '🏆', title: '深睡占比 28%，近 30 天最佳', desc: '深睡是恢复的核心阶段，今天这个数值说明你的身体恢复得非常好。', cta: '了解深睡对精力的影响 ›' },
    ],
    desc: '高能大幅提升场景：睡眠质量优异，深睡、HRV 均创近期新高。',
  },

  morning_down: {
    isNight: false,
    greeting: '早上好',
    statusTime: '9:41',
    metric: { value: '4.8', unit: 'h', deltaClass: 'negative', deltaText: '↓ -2.1h vs 昨天', label: '今日预估高能时长' },
    windows: ['10:30–12:30', '20:00–21:30'],
    digest: '1:30 才睡，深睡只抢到 12%——高能时段集中在上午，先把最重要的事搞定',
    questions: ['为什么睡晚影响这么大', '今天怎么补救', '小睡能提升多少'],
    attrs: [
      { icon: '⏰', name: '入睡时间', value: '凌晨 1:30（晚 2.5h）', contrib: '-1.5h', cls: 'negative' },
      { icon: '💤', name: '深睡占比', value: '12%（↓10%）', contrib: '-0.4h', cls: 'negative' },
      { icon: '🌙', name: '昨夜睡眠时长', value: '5h45m', contrib: '-0.2h', cls: 'negative' },
    ],
    notables: [
      { type: 'negative', badge: '⚠️', title: '静息心率偏高 +8bpm', desc: '今晨静息心率 70bpm，比你的基线高 8bpm，通常和睡眠不足有关。', cta: '了解原因和今日建议 ›' },
    ],
    desc: '高能大幅下降场景：昨晚睡眠严重不足，今日精力预计明显受损。',
  },

  daytime: {
    isNight: false,
    greeting: '下午好',
    statusTime: '14:23',
    metric: { value: '7.5', unit: 'h', deltaClass: 'neutral', deltaText: '→ 与昨天持平', label: '今日预估高能时长' },
    windows: ['09:30–11:45', '18:45–21:10'],
    digest: '还剩 3.8h 高能额度，18:45 是你下午的主场——现在适合做些不费脑的事',
    questions: ['高能剩余怎么看', '14点这么困怎么办', '下午小睡有帮助吗'],
    attrs: [
      { icon: '💤', name: '深睡占比', value: '22%', contrib: '+0.1h', cls: 'positive' },
      { icon: '🏃', name: '今日活动量', value: '步数 4,200', contrib: '中性', cls: 'neutral' },
      { icon: '☕', name: '咖啡因摄入', value: '上午 1 杯（9:30）', contrib: '中性', cls: 'neutral' },
    ],
    notables: [],
    desc: '日间查看场景：用户下午打开 App，快速确认当前状态和接下来的建议。',
  },

  night_ready: {
    isNight: true,
    greeting: '晚上好',
    statusTime: '21:45',
    readiness: { level: 'ready', color: '#34C759', dashOffset: 0, icon: '🟢', label: '已准备好', sub: '' },
    recBedtime: '22:30', tomorrowHe: '7.5h',
    digest: '静息心率已降到 58bpm，身体比你先准备好了——差不多可以开始收工了',
    questions: ['现在做什么帮助入睡', '明天高能时段是几点', '睡前还能喝水吗'],
    attrs: [
      { icon: '❤️', name: '心率趋势', value: '持续下降中 · 58bpm', contrib: '↑ 正向', cls: 'positive' },
      { icon: '☕', name: '距上次咖啡因', value: '8小时前', contrib: '↑ 正向', cls: 'positive' },
      { icon: '🏃', name: '距上次运动', value: '4小时前', contrib: '↑ 正向', cls: 'positive' },
      { icon: '👣', name: '今日活动量', value: '步数 9,200', contrib: '↑ 正向', cls: 'positive' },
    ],
    notables: [],
    desc: '睡前-已准备好：身体状态良好，推荐 22:30 入睡，体验目标是"安心"。',
  },

  night_almost: {
    isNight: true,
    greeting: '晚上好',
    statusTime: '21:45',
    readiness: { level: 'almost', color: '#FF9500', dashOffset: 95, icon: '🟡', label: '接近准备好', sub: '约 25 分钟后最佳' },
    recBedtime: '22:30', tomorrowHe: '7.3h',
    digest: '心率还差一点，大概 25 分钟后会到最佳入睡状态——还有点时间可以收个尾',
    questions: ['怎么加速准备好', '22点睡和22:30有差多少', '晚上刷手机影响多大'],
    attrs: [
      { icon: '❤️', name: '心率趋势', value: '缓慢下降中 · 65bpm', contrib: '→ 中性', cls: 'neutral' },
      { icon: '☕', name: '距上次咖啡因', value: '6小时前', contrib: '→ 中性', cls: 'neutral' },
      { icon: '🏃', name: '距上次运动', value: '2小时前', contrib: '↑ 正向', cls: 'positive' },
      { icon: '📱', name: '蓝光暴露', value: '刚才还在用手机', contrib: '↓ 轻微负向', cls: 'negative' },
    ],
    notables: [],
    desc: '睡前-接近准备好：再等约25分钟进入最佳状态，体验目标是"轻度引导"。',
  },

  night_not_ready: {
    isNight: true,
    greeting: '晚上好',
    statusTime: '21:45',
    readiness: { level: 'not_ready', color: '#FF375F', dashOffset: 220, icon: '🔴', label: '还需准备', sub: '建议做一些放松活动' },
    recBedtime: '23:00', tomorrowHe: '6.8h',
    digest: '心率偏高，身体还处于兴奋状态——试试 5 分钟呼吸练习，有助于加速平静',
    questions: ['5分钟呼吸怎么做', '偏高多少才算正常', '今晚能补救吗'],
    attrs: [
      { icon: '❤️', name: '心率趋势', value: '仍然偏高 · 74bpm', contrib: '↓ 负向', cls: 'negative' },
      { icon: '☕', name: '距上次咖啡因', value: '3小时前（偏近）', contrib: '↓ 负向', cls: 'negative' },
      { icon: '🧘', name: '今日冥想', value: '未进行', contrib: '→ 中性', cls: 'neutral' },
    ],
    notables: [
      { type: 'negative', badge: '⚠️', title: '心率持续偏高', desc: '当前 74bpm，比你入睡基线高约 16bpm。试试 5 分钟 4-7-8 呼吸法可快速降低心率。', cta: '查看具体方法和今晚建议 ›' },
    ],
    desc: '睡前-未准备好：身体仍处兴奋状态，需要行动来加速准备，才出现建议。',
  },

  syncing: {
    isNight: false, isSyncing: true,
    greeting: '早上好', statusTime: '9:41',
    metric: { value: '—', unit: '', deltaClass: 'neutral', deltaText: '同步中...', label: '正在获取数据' },
    windows: [], digest: '', questions: [], attrs: [], notables: [],
    desc: '数据同步中：App 正在从健康数据同步最新数据，展示上次缓存值。',
  },

  first_use: {
    isNight: false, isFirstUse: true,
    greeting: '早上好', statusTime: '9:41',
    desc: '首次使用：引导用户了解高能时长概念。',
  },
};

// Today tab mock data (shared across today-tab scenes)
const TODAY_PINS = [
  { id: 'p1', type: 'caffeine', icon: '☕', label: '喝咖啡', time: '10:30 前', dosage: '1 杯', impact: '+0.3h', reason: '10:30 前摄入咖啡因不影响晚间睡眠，且在第一高能时段的尾段补充效果最好。', timeH: 10.5, energyPct: 0.45 },
  { id: 'p2', type: 'exercise', icon: '🏃', label: '运动', time: '17:00–18:00', dosage: '30min', impact: '+0.5h', reason: '下午运动可拉长傍晚高能时段，且不影响当夜入睡。', timeH: 17.5, energyPct: 0.3 },
  { id: 'p3', type: 'nap', icon: '😴', label: '小睡', time: '14:00 前', dosage: '20min', impact: '+0.4h', reason: '14:00 前的 20 分钟小睡是精力的"充电宝"，过晚会影响夜间睡眠质量。', timeH: 13.5, energyPct: 0.25 },
  { id: 'p4', type: 'sleep', icon: '🌙', label: '准备入睡', time: '22:30', dosage: null, impact: null, reason: '按推荐时间入睡可保证明日高能时长最大化。', timeH: 22.5, energyPct: 0.1 },
];

// Energy curve points: [hour, energyLevel 0-1]
// representing a typical good-sleep day
const CURVE_POINTS = [
  [6,0.15],[7,0.35],[8,0.55],[9,0.72],[9.5,0.85],[10.5,0.9],[11,0.88],[11.5,0.82],[12,0.65],
  [13,0.45],[13.5,0.32],[14,0.28],[14.5,0.3],[15,0.38],[16,0.5],[17,0.6],[18,0.72],[18.5,0.82],
  [19.5,0.88],[20,0.85],[20.5,0.8],[21,0.72],[21.5,0.55],[22,0.35],[22.5,0.2],[23,0.1],[24,0.05]
];

// High energy windows (hour ranges)
const HIGH_ENERGY_WINDOWS = [[9.5, 11.75], [18.5, 21.17]];
