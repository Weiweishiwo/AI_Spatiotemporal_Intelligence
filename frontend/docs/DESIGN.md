## Vibe
- 明亮雾蓝科技（Swiss functionalism × blueprint line work）：面向政企 B 端工业巡检，克制冷静、信息清晰、留白充足

## Color
- Primary: #1E5C8C
- On Primary: #FFFFFF
- Accent: #0E8A8A
- On Accent: #FFFFFF
- Background: #F4F7FA
- Foreground: #1B2A3A
- Muted: #E7EEF4
- Border: #D6E1EC
- Secondary: #DCE7F1

## Typography
- Heading: AlibabaPuHuiTi (family: 'AlibabaPuHuiTi', weight: 600, url: https://resource-static.bj.bcebos.com/fonts-skill/AlibabaPuHuiTi_SemiBold.ttf)
- Body: AlibabaPuHuiTi (family: 'AlibabaPuHuiTi', weight: 400, url: https://resource-static.bj.bcebos.com/fonts-skill/AlibabaPuHuiTi_Regular.ttf)

## Visual Language
- 核心视觉签名：蓝图细线网格 + 流动巡检轨迹（SVG path 沿路径流动的虚线偏移动画）+ 扫描波纹（同心圆环缓慢扩散淡出），构成园区数字孪生巡检的专属视觉语言
- 材质与深度：纯白卡片浮于浅雾蓝灰底之上，靠极细边框（1px 雾蓝）与柔和投影分层，禁用毛玻璃光晕
- 容器与按钮：卡片 rounded-2xl + 细边框；主按钮 Primary 实底；次按钮 Muted 底 + Foreground 字；图标用 lucide-react 线性图标
- 布局节奏：大留白网格，模块间充足留白，强调色仅落在按钮/激活态/数据高亮/轨迹线条等小面积

## Animation
- 入场：模块随滚动平滑淡入上移，错落时序，缓动 ease-out，时长 500-700ms
- 交互：按钮轻微位移与阴影变化，hover 时轨迹流动加速
- 滚动/过渡：Hero 右侧巡检轨迹沿路径持续流动、扫描波纹循环扩散、数据卡片数值轻微计数跳动

## Forbidden
- 禁用深色背景与霓虹/赛博/暗黑光晕效果
- 禁大块纯色铺底（Hero/Banner/操作区），Primary/Accent 仅小面积焦点
- 禁 Emoji 图标、粒子爆炸等花哨特效、毛玻璃彩色光斑