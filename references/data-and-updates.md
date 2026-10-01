# 数据与更新

mapPlaces 保存provider地点绑定、核实来源、日期及入口/地址差异；事件、住宿、食品通过 mapPlaceKey 引用。字段与回退规则见 map-navigation.md；未知或歧义地点继续查找，不猜分店，也不自动启动驾车导航。

每日预览增加 previewTitle/previewSummary/previewIcon，过夜城市使用 overnightCity；完整订单增加 tickets/groundOrders/otherOrders、bookingState 与各类详情字段。字段及动效行为见 preview-motion-and-orders.md。保留稳定订单id和用户原始状态；公开版从脱敏源数据生成，bookingReference 默认不展示。

地图新增 geographicMap.cities 的 country/role、focusCountry/focusIndices/focusLabel 与 onlineTiles 开关；自动生成游玩区域大图和出入境小图。交通插画继承只在渲染时计算 displayMode/inherited/sourceLeg，不回写 mode。详见 components-and-maps.md。

项目目录包含 trip.json、index.html、history/ 与 sources（如有外部研究）。默认构建命令：python scripts/build_original.py 项目/trip.json 项目/index.html；脚本和模板路径相对 Skill 目录解析，不依赖作者电脑路径。build.py 为早期简化实验，不作默认交付。

visualTheme.stylesheet 是项目内目的地装饰 CSS 的相对路径；生成器直接内嵌并将固定组件与控件状态契约置于其后。换主题只改 palette、装饰与 styleVersion，不改旅行内容。配色回归按 theme-isolation.md，项目不能通过事后追加覆盖替代包内修复。

扩展字段：countdowns（title/at/note，at 必须含明确时区）；transports（mode/from/to/departure/arrival/status/note）；routeNodes（label/x/y/mode，当前 x/y 是拓扑示意位置）；titleArt、avatarAsset（项目内相对资产路径）；foodImages（图像键到项目相对路径）；days[].food 与 foodNote；tips（title/detail）；mapProvider（google/amap）。食品记录：image/kind/title/desc/shop/shopUrl/xhs。模式不得仅从国际去程推断全程交通。

新增：mapProviders 按城市覆盖（大陆 amap、境外 google）；routeSegments 按真实路线顺序保存 from/to/mode（plane/train/car/bike/unknown）和 source（用户输入或演示），不能靠外观选择改变事实；visualTheme.palette 与 basis 保存主题；destinationTheme=thailand-summer 仅为可选示例。食品可加 city/address/imageType/checkedAt/shopLinkLabel/xhsUrl/dianpingUrl，真实资料链接与搜索入口分开。foodImages 的值也可为 {path,viewBox,width,height}，用 SVG 视口排布已有素材，图片生成/抠图仍交给可用生图工具。

trip 字段：title、subtitle、origin、duration、timezone、dates、flight、contentVersion、styleVersion、theme、days、bookings、conflicts、pending、sources。theme 含 direction（a/b）、large（布尔）。每一天含稳定 id、number、city、status、summary、events（id/title/detail/status）。预订含 id、city、nights（第几晚）、name、address、synthetic、status；测试预订的“已订”仅代表情境，不是现实订单。

每次改动保存完整快照和用户消息。内容与主题分别追踪；生成器不得修改源数据。sources 存标题、URL、查验日期和支持的字段；主题推断不能写成文化事实。页面内 JSON 用安全序列化，用户文本用 textContent 或 HTML 转义。

sources 使用 {title,url,checkedAt,supports:[支持的信息]}；生成器自动展示来源与事实边界。跨城日 city 是展示文字，不用作导航城市：每个 events[].city 和 food[].city 必须是单一真实城市，也可用 days[].navigationCity 作为当天地点默认值。没补城市的跨城事件保留文字与待办，暂不提供错误导航。transports/routeSegments 的已知方式及状态自动进入订单摘要，不把“偏好高铁、车次未订”退化为“方式未知”。

持续更新检查：提前城市转移时比较当地过夜城市与所有已订酒店；未知夜晚也保留。拒绝静默取消。跨时区交通保留当地日期、时区和绝对时刻；没有日期不生成真实倒计时。回退必须指向稳定快照，样式回退只恢复 theme/styleVersion。
