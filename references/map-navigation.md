# 地图地点绑定与跳转验收

生成器已接入 map-navigation.js、map-navigation.css 和 navigation_places.py；酒店、活动地点和今日吃什么共用入口。基础跳转不需要用户安装其他 Skill，也不需要地图 API Key。检索具体地点编号可能需要宿主联网或已有授权工具，不能把“链接不需要Key”说成“自动查询所有地点不需要能力”。

## 优先级与地点身份

中国大陆默认高德，境外默认Google Maps；混合行程逐城市选择 mapProviders，用户可明确覆盖。先核对店铺/酒店具体分店、城市、地址和地图登记名；保持订单文字与地图登记名分别记录，不静默更改订单地址。入口、停车场、景区范围点与酒店前台可能不同，查看地点详情不等于确认了可通行入口。

优先使用核实的 provider 地点编号或用户提供且核对一致的官方分享链接。高德：poidetail + poiid；Google：search + api=1 + query + query_place_id，query 保留官方登记名称和城市作为后备。没有编号时，可以使用经核实的Google WGS84地点坐标，界面标为参考点；不能把高德GCJ02或城市中心直接当作Google入口。没有可靠绑定就提供名称查找，使用具体分店名与城市，避免把名称、整段订单地址和备注合成超长关键词。

不使用模糊名称匹配猜地点。相同城市中多个同名记录且未明确 key 时回退查找；跨城市、跨服务的编号绝不混用。不把机场/城市图上的粗坐标自动作为酒店坐标。不默认启动驾车导航，保留用户决定出行方式和核对入口的步骤。

## 数据

trip.json 的 mapPlaces 是地点记录数组。每条包含 key（项目内稳定标识）、provider（amap/google）、name（地图登记名）、city（单一城市）、aliases（已核对的显示名称别名数组），可有 placeId、shareUrl 或 coordinates={lat,lon,crs}，以及 note/addressReview/referenceOnly。verified=true 必须同时提供 checkedAt 和 source（核实依据）；sourceUrl 可记录公开资料链接。synthetic 不得作为已核实记录。构建验证坐标、链接服务、字段类型与重复key，缺依据保留待核实查找。

事件 events[]、住宿 bookings[]、食品 food[] 使用 mapPlaceKey 指向记录；显示名称与地图名不同优先显式绑定key。酒店/店铺可以用 mapQuery 指定准确分店名，保持原名称、订单地址和来源。所有编号仅在同一 provider、同一 city 下生效。不要把作者原有旅行的地点编号、地址、API凭据硬编码进基础包。

Google Maps URL示例（官方公开示例，非用户目的地）：

```json
{"key":"lumen","provider":"google","name":"Lumen Field","city":"Seattle","aliases":["卢门球场"],"placeId":"ChIJKxjxuaNqkFQR3CK6O1HNNqY","verified":true,"checkedAt":"2026-10-01","source":"Google Maps URLs official example"}
```

构建成 `https://www.google.com/maps/search/?api=1&query=...&query_place_id=...`。编号必须来自核实，不模仿示例编造。用户只需给计划和后续补充信息，助手整理这些字段，不要求用户填写内部JSON。

## 备用与设备差异

点击后保留同地点的备用入口与复制名称。高德备用链接 callnative=0，主入口 callnative=1；后备不得丢失poi编号。Google 使用跨平台HTTPS链接，是否进入App由安装状态和浏览器处理决定；不提供不存在的“强制网页版”参数，也不把新窗口当作强制网页保证。页面标为“备用地图入口”，必要时说明复制到系统浏览器/地图搜索。

只有官方分享链接而没有编号时，备用入口保留原分享链接，不能退回相似名称搜索丢失地点身份。高德uri链接可设置callnative；无法控制App接管的短分享链接统一标为备用入口，不承诺网页版。

微信等内置浏览器提示在系统浏览器打开或复制名称。剪贴板被拒绝时先尝试浏览器复制，再提供可手动选择的名称，不能假报已复制。所有备用控件保留44px触摸区域和主题样式；不使用定时反复跳转，不用失败重试自动把用户带离路书。

## 检查与证据边界

检查酒店、景点、食品入口均带正确服务、城市和绑定key；中文/当地语言/特殊字符正确编码，Google api=1与query始终存在，长链接不超2048字符。未核实地址、模糊分店、跨城日和参考点有可见提示。断网保存的HTML仍可显示与复制，外部地图依然需网络；导出清理运行时备用面板并在重开后重新绑定按钮。

依次区分：本地页面及参数正确、HTTP可访问和编号保留、地图实际渲染为预期地点、真实iOS/Android App接管。每一层单独记结果。网页200或模拟手机UA不证明App打开正确；没有设备或网络受限时明确未验证。地图加载失败不能静默换成另一个地点。

官方规范（核对日期2026-10-01）：[Google Maps URLs](https://developers.google.com/maps/documentation/urls/get-started)、[高德地点详情](https://lbs.amap.com/api/uri-api/guide/mobile-web/information)、[高德搜索](https://lbs.amap.com/api/uri-api/guide/search/search)。规范会变化，处理新故障时重新核对。
