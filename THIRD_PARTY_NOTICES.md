# 素材与第三方来源

项目自有内容按根目录 `LICENSE` 提供。以下第三方数据保留各自许可，不因本项目的非商业许可改变。

## Natural Earth

- `assets/world-land.geojson`：Natural Earth 110m 国界/陆地轮廓。
- `examples/japan/assets/land-10m.geojson`：Natural Earth 10m 陆地轮廓。
- 来源：[Natural Earth](https://www.naturalearthdata.com/)；[原始矢量数据](https://github.com/nvkelso/natural-earth-vector)。
- 许可：[Public Domain](https://www.naturalearthdata.com/about/terms-of-use/)。包内轮廓用于路线概览，并非街道导航数据。

## GeoNames

日本示例中的城市名称及经纬度参考 GeoNames，逐项来源与原查验日期保存在 `examples/japan/trip.json`。

- 来源：[GeoNames](https://www.geonames.org/about.html)。
- 许可：[CC BY 4.0](https://creativecommons.org/licenses/by/4.0/)。示例对城市字段作选取与结构化整理；保留 GeoNames 署名。

## OpenStreetMap

生成器可按配置加载在线 OpenStreetMap 瓦片；本公开日本示例关闭在线瓦片，仅内嵌 Natural Earth 轮廓。安装包未包含下载的街道瓦片。

启用在线瓦片时须保留 © OpenStreetMap contributors，并遵守其[署名与许可说明](https://www.openstreetmap.org/copyright)和[瓦片使用政策](https://operations.osmfoundation.org/policies/tiles/)。

## 插画与链接

日本标题及菜品 SVG 为本项目制作的示意插画，不是实景或店铺照片。代码与页面中的官方旅游、交通和餐饮链接用于指向信息来源，不代表品牌授权或合作。未打包第三方 Skill 全文、远程照片或私有旅行订单。

第三方许可核对日期：2026-10-02。
