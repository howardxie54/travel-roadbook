# 每日预览、动效与订单

这些组件随基础包交付，不需要用户另装设计或动效 Skill。默认生成器 build_original.py 已接入 preview_cards.py、day-motion.js、tablet-and-motion.css、order_sections.py 和 orders.css。换目的地时改变主题参数与内容，保留经过检查的组件行为。

## 每天的预览不是城市名列表

从当天实际活动提炼 previewTitle（建议6–12个汉字的主题）、previewSummary（建议25–50个汉字的小总结），设置 previewIcon。用户只需说行程，助手负责整理字段。总结应体现当天节奏、主要活动或转移及关键待确认项，不能把未确定的活动、酒店、交通写成已落实。信息不足时使用如“先安顿行李，后续活动待补充”；不要编造卖点来填满版面。

图标枚举 plane/train/car/bike/coast/nature/landmark/city/food/rest/route，使用包内一致的描边 SVG。图标说明当天内容，与地图上的交通角色是两种用途。未指定时生成器从已提供的文字提取，缺线索使用中性路线图标。城市完整换行；主题和总结独占宽度，不为箭头或日期挤成省略号。展开内容也展示当天主题、总结和图标。

1–4天用网格卡片，奇数最后一项填满余列；5天及以上用可滚动的完整列表，不堆砌密集网格。每行只有一个44px展开指示控件，点击本行在本行下面展开，再次点击收起；抽屉内部仅保留“查看完整行程”，不添加第二个收起按钮。日期导航水平排列，完整文字可换行。必须在3/6/7/8/9/10/11/14天及320/390/桌面宽度检查实际页面，不靠截图猜测。

## 动效随内容，不随固定天数

复用 day-motion.js：当前页跟手，拖动不足38%时邻页透明，38%–56%逐渐出现，超过裁切视口的一半才切换，否则回到本页。收尾约260ms，沿用主题统一的 --ease-out，不额外弹跳。平移距离按裁切视口测量，包含留白；布局宽度按面板真实尺寸保存，不能取整。旧页完全滑出后再隐藏并清理动画，避免残影与文字重新排版。

所有索引用实际 trip.length，不能硬编码4天。快速操作允许中断或排队；边界只能轻微移动，不循环到另一端。待进入的邻页 inert、aria-hidden 且不可点击，结束后恢复。取消、第二根手指、缩放、丢失捕获、横竖屏与后台切换需要清理。丢失捕获只监听实际捕获容器，不能把子元素的隐式捕获转移当作取消整个手势。

减少动态效果与键盘切换直接完成，保持按键焦点、选中态及日期同步。手机与触摸平板保留底部导航；平板竖屏时间线一列、美食在下方，横屏按空间采用双列。1360px以上且侧边留白足够时才显示桌面右栏。测试需覆盖真实触摸及Chrome/WebKit；模拟WebKit通过不等于真实iPhone Safari已验证。

## 订单是一等内容

examples/order-fields-example.json 提供可运行的虚构字段示例，仅作结构参考，不能当作用户行程或真实订单。

始终保留交通、住宿、门票/预约三组，未知时明确待补充。按输入增加租车/接送和其他旅行订单（例如用户提供的保险记录），不凭空新增消费或预约。集合与衔接保留独立位置。摘要展示路线、日期/时刻和状态，更多字段使用一致的原生 details 控件，键盘可打开，保持完整文字与主题配色。

助手从用户授权提供的文本、截图或文件提取，不要求用户填写内部JSON。稳定id用于持续更新，bookingState 使用 confirmed/pending_payment/planned/unknown/cancelled/not_needed；status 保留原文。仅已付款不自动等于已出票，用户偏好不等于订单成功。矛盾的文字状态暂作未知，追问需要解决的事实；synthetic 测试数据必须可见标记。

共同字段：id、status、bookingState、price、currency、paymentStatus、cancellation、note，以及经核实可公开的 officialUrl。规则、价格、行李额只记录用户给出的事实或有来源的公开资料，不生成默认承诺。

- transports：mode/from/to、date/arrivalDate、departure/arrival、timezone/arrivalTimezone、carrier、number、departurePlace/arrivalPlace、departureTerminal/arrivalTerminal、seatClass、baggage、checkInDeadline。
- bookings：name/city/address、nights（第几晚）、checkIn/checkOut、timezone、roomType、rooms、guests（人数）、breakfast、checkInTime、contact（酒店公开联系方式）。不完整、虚构或未知地址不能提供导航。
- tickets：title、city、date、time、timezone、place（入口/集合点）、quantity。
- groundOrders：title、pickup/pickupAt、returnPlace/returnAt、provider，必要时补时区。
- otherOrders：title、provider、coverage、validFrom/validUntil，只记录实际提供的产品内容。
- meeting：time、timezone、place、group、note，不从航班起飞时刻直接推算集合时间。

每天提供 overnightCity 时，生成器与已确认酒店的 nights/city 对照，发现冲突后保留原订单与冲突提醒。跨城日的展示文字不能代替过夜城市；不清楚是往返还是换酒店时向用户确认。已取消的订单保留历史状态，但不作为活跃住宿冲突。输入数据保持不变，新的完整快照保存内容与样式版本。

## 公开与私用

默认不渲染 bookingReference；私用且明确需要时 includePrivateOrders=true 可以展示。shareMode=public 即使这个标志开启也禁止展示。此开关只处理参考号，不能替代整体脱敏：输出包含行程JSON，需先从公开版源数据移除姓名、证件、电话、付款码、PNR、管理订单链接及自由备注中的敏感信息，再生成网页和截图。不能靠隐藏HTML来脱敏，也不能承诺会自动识别所有敏感文字。

检查订单数量与id是否一致，日期/时区/金额有无丢失，取消/待付款状态有无误变，虚构酒店是否出现导航，原生折叠是否可操作，公开源码及下载文件是否包含私人字段。订单数据改变不应意外重置页面主题、地图交通动画或其他天的内容。
