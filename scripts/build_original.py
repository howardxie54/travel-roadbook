"""Build the preserved roadbook UI from portable data and optional local artwork."""
import base64
import html
import json
import math
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
esc = lambda x: html.escape(str(x))


def svg_image(text, color, background):
    svg = '<svg xmlns="http://www.w3.org/2000/svg" width="1000" height="390"><rect width="1000" height="390" fill="'+background+'"/><text x="500" y="250" text-anchor="middle" font-family="serif" font-size="150" fill="'+color+'">'+esc(text)+'</text></svg>'
    return 'data:image/svg+xml;base64,'+base64.b64encode(svg.encode()).decode()


def local_image(filename, directory):
    path = (directory / filename).resolve()
    # Local project assets only; remote images must be obtained under their rights.
    if directory.resolve() not in path.parents:
        raise ValueError('Asset must be inside project directory')
    mime = {'.svg':'image/svg+xml','.png':'image/png','.webp':'image/webp','.jpg':'image/jpeg','.jpeg':'image/jpeg'}[path.suffix.lower()]
    return 'data:'+mime+';base64,'+base64.b64encode(path.read_bytes()).decode()


def build(data, output, directory):
    from normalize_input import normalize
    data=normalize(data)
    template = (ROOT / 'assets' / 'original-template.html').read_text(encoding='utf-8')
    template=template.replace('const config=__CONFIG__;\nconst trip=config.days;','')
    template=template.replace('const foodImages=', 'const config=__CONFIG__;const trip=config.days;\nconst foodImages=',1)
    template=template.replace('const foodImages=__FOOD_IMAGES__;', (ROOT/'assets'/'image-assets.js').read_text(encoding='utf-8'))
    renderer=(ROOT/'assets'/'food-renderer.js').read_text(encoding='utf-8')
    template=re.sub(r'function foodHtml\(f\)\{.*?\n    function dayHtml',lambda _:renderer+'\n    function dayHtml',template,count=1,flags=re.S)
    from preview_cards import details as preview_details,icon as preview_icon,cards as preview_cards
    days=[]
    for d in data['days']:
        foods=d.get('food',[])
        if not foods:
            foods=[dict(image='placeholder',kind='推荐待补充',title=d['city']+' · 吃什么',desc='保留推荐板块；待提供口味偏好或核实资料后补充菜品与店铺，不虚构推荐结果。',shop='',shopUrl='',xhs=d['city']+' 美食')]
        stops=[]
        for i,e in enumerate(d['events']):
            navigation_pending=bool(e.get('_navigationPending'))
            stops.append(dict(time=e.get('time','待定'),title=e['title'],text=e['detail'],detail='信息状态：'+e['status']+(' · 地点城市待补充，暂不提供导航' if navigation_pending else ''),status=e['status'],key=i==0,noMap=not e.get('place') or navigation_pending,place=e.get('place',''),city=e.get('city',d['city']),mapPlaceKey=e.get('mapPlaceKey','')))
        days.append(dict(date='第 '+str(d['number'])+' 天',subtitle=d['city'],distance=d['status'],focus=d.get('focus','当天重点 · '+d['city']),focusText=d['summary'],alert=d.get('alert') or ('；'.join(data['conflicts']) if data['conflicts'] else '具体时间、交通与活动待补充；暂定内容不代表已经预订。'),stops=stops,food=foods,foodNote=d.get('foodNote','先确认当天路线与用餐窗口，再补充顺路推荐。')))
    for day,rendered in zip(data['days'],days):
        p=preview_details(day)
        rendered.update(previewTitle=p['title'],previewSummary=p['summary'],previewIconSvg=preview_icon(p['icon']))
    route_cities=data.get('geographicMap',{}).get('cities',data.get('routeNodes',[{'label':data['origin']},{'label':data['days'][0]['city']}]))
    segments=data.get('routeSegments')
    if not segments:
        aliases={'飞机':'plane','火车':'train','高铁':'train','汽车':'car','自驾':'car','自行车':'bike'}
        segments=[]
        for a,b in zip(route_cities,route_cities[1:]):
            match=next((t for t in data.get('transports',[]) if t.get('from')==a['label'] and t.get('to')==b['label']),{})
            segments.append(dict(mode=aliases.get(match.get('mode'),match.get('mode','unknown')),**{'from':a['label'],'to':b['label']}))
    config=dict(days=days,countdowns=data.get('countdowns',[]),mapProvider=data.get('mapProvider','amap' if data.get('country')=='CN' else 'google'),mapProviders=data.get('mapProviders',{}),longItinerary=data['duration']>4,routeSegments=segments)
    template=template.replace("config.mapProvider==='amap'", "(config.mapProviders[city]||config.mapProvider)==='amap'")
    template=template.replace("encodeURIComponent(q+' '+city)}&view=list", "encodeURIComponent(q)}&city=${encodeURIComponent(city)}&view=list&src=travel-roadbook")
    config['routeCities']=[c['label'] for c in route_cities]
    config['mapPlaces']=data['mapPlaces']
    navigation=(ROOT/'assets'/'map-navigation.js').read_text(encoding='utf-8')
    template,n=re.subn(r'    const mapUrl=.*?(?=    const xhsUrl=)',lambda _:navigation+'\n',template,count=1,flags=re.S)
    if n!=1:raise ValueError('Map navigation template integration failed')
    template=template.replace('href="${mapUrl(s.place,s.city)}"','data-roadbook-map data-map-query="${esc(s.place)}" data-map-city="${esc(s.city)}" data-map-key="${esc(s.mapPlaceKey||\'\')}" href="${esc(mapUrl(s.place,s.city,true,s.mapPlaceKey))}"')
    template=template.replace('href="${mapUrl(s.altPlace,s.city)}"','data-roadbook-map data-map-query="${esc(s.altPlace)}" data-map-city="${esc(s.city)}" href="${esc(mapUrl(s.altPlace,s.city))}"')
    template=template.replace("<span>查地点</span>","<span>${mapTarget(s.place,s.city,true,s.mapPlaceKey).mode==='place'?'查看地图地点':mapTarget(s.place,s.city,true,s.mapPlaceKey).mode==='point'?'查看地图参考点':'查找地点'}</span>")
    template=template.replace("document.getElementById('days').innerHTML=trip.map(dayHtml).join('');","document.getElementById('days').innerHTML=trip.map(dayHtml).join('');bindMapRecovery();")
    cards=preview_cards(data['days'])
    tabs=''.join('<button class="day-tab" type="button" data-day="'+str(i)+'" id="day-tab-'+str(i)+'" role="tab" aria-controls="day-panel-'+str(i)+'" tabindex="'+('0' if i==0 else '-1')+'" aria-selected="'+str(i==0).lower()+'">第 '+str(i+1)+' 天<b>'+esc(d['city'])+'</b></button>' for i,d in enumerate(data['days']))
    from order_sections import render as render_orders
    inferred=[dict(segment,**{'from':segment.get('from') or route_cities[min(i,len(route_cities)-1)]['label'],'to':segment.get('to') or route_cities[min(i+1,len(route_cities)-1)]['label']}) for i,segment in enumerate(segments)]
    booking=render_orders(data,inferred)
    # Spatially neutral topology, explicitly not a geographic basemap.
    nodes=data.get('routeNodes',[dict(label=data['origin'],x=110,y=105,mode='unknown'),dict(label=data['days'][0]['city'],x=450,y=410,mode='unknown')])
    config['modes']=[n.get('mode','unknown') for n in nodes[:-1]]
    legs=['M{0} {1} Q{2} {3} {4} {5}'.format(a['x'],a['y'],(a['x']+b['x'])/2+35,(a['y']+b['y'])/2-30,b['x'],b['y']) for a,b in zip(nodes,nodes[1:])]
    loop=' '.join(legs)
    from theme_tokens import palette
    colors=palette(data)
    title_color=colors['accent']
    title_art=local_image(data['titleArt'],directory) if data.get('titleArt') else svg_image(data.get('visualLine','旅途之间'),title_color,colors['accent-soft'])
    avatar='<circle cx="0" cy="-14" r="7" fill="var(--surface)" stroke="var(--accent)" stroke-width="3"/><path d="M0 -6V15M-12 3L0 -3 12 3M0 15L-9 29M0 15L9 29" fill="none" stroke="var(--accent)" stroke-width="4" stroke-linecap="round"/>'
    if data.get('avatarAsset'):
        avatar='<image href="'+local_image(data['avatarAsset'],directory)+'" x="-35" y="-40" width="70" height="80"/>'
    route='<svg class="route-map" id="route-map" viewBox="0 0 600 545" role="img" aria-labelledby="route-map-title route-map-desc"><title id="route-map-title">旅行路线示意</title><desc id="route-map-desc">示意位置，不代表真实地理坐标或道路；交通方式未确认的区段用中性标识。</desc><rect width="600" height="545" fill="var(--accent-soft)"/><path d="M0 340Q220 310 600 510V545H0Z" fill="var(--line)"/><path id="route-loop" d="'+loop+'" fill="none" stroke="none"/><use href="#route-loop" class="route-underlay"/>'+''.join('<path class="route-leg" data-leg="'+str(i)+'" d="'+leg+'"/>' for i,leg in enumerate(legs))+'<g class="map-nodes">'+''.join('<circle class="map-dot" cx="'+str(n['x'])+'" cy="'+str(n['y'])+'" r="8"/>' for n in nodes)+'</g><g class="map-labels">'+''.join('<text x="'+str(n['x'])+'" y="'+str(n['y']+43)+'" text-anchor="middle" class="map-label">'+esc(n['label'])+'</text>' for n in nodes)+'</g><g id="route-traveler"><g id="route-heading">'+avatar+'<text id="transport-mode" x="0" y="-45" text-anchor="middle" font-size="16">✈</text></g></g></svg>'
    values=dict(BRAND=data['title']+' · 旅行路书',PERIOD=data.get('dates') or str(data['duration'])+' 天 · 日期待定',ORIGIN=data['origin']+'出发 · 交通可补充',INTRO=data['subtitle'],TITLE=data.get('visualLine','旅途之间'),ROUTE_TITLE=str(data['duration'])+' 天的路线',ROUTE_SUBTITLE='行程可逐步补充',MAP_STATUS='路线示意 · 交通待确认',MAP_ATTRIBUTION='示意图 · 非地理底图',ROUTE_CAPTION='连线仅表示城市间的旅行顺序，不代表实际道路或精确地理位置。交通方式与返程线路待确认。',DISCLAIMER=data.get('disclaimer','未知信息已标注，请出发前核实。'))
    for key,value in values.items():
        template=template.replace('__'+key+'__',esc(value))
    images={'placeholder':svg_image('推荐待补充',title_color,colors['accent-soft'])};resources={}
    for key,value in data.get('foodImages',{}).items():
        if isinstance(value,dict):
            box=[float(v) for v in value['viewBox'].split()]
            if len(box)!=4 or not all(math.isfinite(v) for v in box) or min(box[2:])<=0:raise ValueError('Food crop viewBox must contain four finite numbers and positive dimensions')
            if not all(isinstance(value[k],(int,float)) and math.isfinite(value[k]) and value[k]>0 for k in ('width','height')):raise ValueError('Food image dimensions must be positive numbers')
            resources.setdefault(value['path'],local_image(value['path'],directory))
            images[key]=dict(resource=value['path'],viewBox=' '.join(map(str,box)),width=value['width'],height=value['height'])
        else:
            images[key]=local_image(value,directory)
    raw=dict(CONFIG=json.dumps(config,ensure_ascii=False).replace('<','\\u003c'),ROUTE_CARDS=cards,DAY_TABS=tabs,BOOKING=booking,TODO=''.join('<li>'+esc(x)+'</li>' for x in data['conflicts']+data['pending']),TIPS=''.join('<div class="card tip"><b>'+esc(t['title'])+'</b><p>'+esc(t['detail'])+'</p></div>' for t in data.get('tips',[dict(title='先确认城市间交通',detail='换城市的日期与住宿夜晚需要对齐。'),dict(title='留出机场衔接',detail='收到真实航班与交通资料后再确定缓冲。'),dict(title='推荐可以继续补',detail='按当天活动与饮食偏好补充，不为吃饭增加绕行。'),dict(title='核对住宿与路线',detail='提前换城市后，请确认预订是否需要改动。')])),ROUTE_SVG=route,IMG_TITLE_ART=title_art,FOOD_IMAGES=json.dumps(dict(images=images,resources=resources),ensure_ascii=False).replace('<','\\u003c'))
    for key,value in raw.items():
        template=template.replace('__'+key+'__',value)
    sources=[]
    for source in data.get('sources') or []:
        url=source.get('url','');title=esc(source.get('title','参考资料'))
        label='<a href="'+esc(url)+'" target="_blank" rel="noopener noreferrer">'+title+'</a>' if re.match(r'^https?://',url,re.I) else title
        support=source.get('supports') or source.get('supportsFields') or []
        detail='；'.join(map(str,support)) if isinstance(support,list) else str(support)
        sources.append('<li>'+label+'<p>'+esc(detail)+(' · 查验 '+esc(source['checkedAt']) if source.get('checkedAt') else '')+'</p></li>')
    if sources:
        section='<details class="card sources-section"><summary>资料来源与事实边界</summary><ul>'+''.join(sources)+'</ul><p>设计主题为审美推断；营业、交通与预订情况请出发前复核。</p></details>'
        template=template.replace('<footer>',section+'<footer>',1)
    template=template.replace('<head>','<head><style>.daynav .shell{overflow-x:auto}.day-tab{flex:0 0 110px;min-width:110px}.route-grid{grid-template-columns:repeat(auto-fit,minmax(135px,1fr))}.route-map .route-leg{stroke:var(--accent);stroke-width:5;fill:none}#route-heading{transform-box:fill-box}'+('body{font-size:18px}.stop-body p,.food-content p,.alert{font-size:16px!important}' if data['theme'].get('large') else '')+'</style>')
    template=template.replace('</head>','<style>.daynav .shell{flex-wrap:nowrap!important;overflow-x:auto}.day-tab{flex:0 0 120px!important;min-width:120px!important}.day-tab b{white-space:nowrap;overflow:hidden;text-overflow:ellipsis}.food-card img[src^="data:image/svg"]{object-fit:contain;background:var(--accent-soft)}</style></head>')
    template=template.replace("routeHeading.setAttribute('transform','rotate('+travelerTilt+') scale('+travelerFacing+' 1)');", "routeHeading.setAttribute('transform','');let passed=0,index=0;for(let j=0;j<routeLegLengths.length;j++){passed+=routeLegLengths[j];index=j;if(distance<=passed)break}document.getElementById('transport-mode').textContent=({plane:'✈',train:'火车',car:'汽车',boat:'船',walk:'步行'})[config.modes[index]]||'↔';")
    if data.get('destinationTheme')=='thailand-summer':
        from destination_design import apply_design
        template=apply_design(template,data,directory,local_image)
    else:
        from theme_tokens import palette
        colors=palette(data)
        css=':root{'+''.join('--'+key+':'+value+';' for key,value in colors.items())+'}'+(ROOT/'assets'/'portable.css').read_text(encoding='utf-8')
        template=template.replace('</head>','<style>'+css+'</style></head>')
        hero='<section class="intro portable-hero" aria-labelledby="page-title"><div class="hero-kicker">'+esc(data.get('themeLabel',data['title']+' · 旅行手记'))+'</div><h1 id="page-title">'+esc(data.get('displayTitle') or data.get('visualLine') or data['title'])+'</h1><p>'+esc(data['subtitle'])+'</p><div class="trip-seal"><b>'+str(data['duration'])+' 天</b><span>'+esc(data['origin']+'出发 · '+(data.get('dates') or '日期待定'))+'</span></div>'+('<img class="hero-artwork" src="'+title_art+'" alt="" aria-hidden="true">' if data.get('titleArt') else '')+'</section>'
        template=re.sub(r'<section class="intro".*?</section>',lambda _:hero,template,count=1,flags=re.S)
        template=re.sub(r'<script>\s*\(\(\)=>\{\s*const reduce=matchMedia.*?</script>','',template,count=1,flags=re.S)
        template=template.replace('<div class="route-grid">','<div class="route-grid'+(' long-itinerary' if data['duration']>4 else '')+'">')
        template=template.replace('function renderRoutePreview(day){const d=trip[day]',"function renderRoutePreview(day){if(config.longItinerary){routeCards[day].insertAdjacentElement('afterend',routePreview)}const d=trip[day]")
        script=(ROOT/'assets'/'adaptive-interactions.js').read_text(encoding='utf-8')
        template=template.replace('</body>','<script>'+script+'</script></body>')
    if data.get('geographicMap') and data.get('destinationTheme')!='thailand-summer':
        from geographic_map import map_svg
        atlas=local_image(data['transportAtlas'],directory) if data.get('transportAtlas') else ''
        template=re.sub(r'<svg class="route-map".*?</svg>',lambda _:map_svg(data,directory,atlas),template,count=1,flags=re.S)
        template=template.replace('示意图 · 非地理底图','© OpenStreetMap contributors · Natural Earth 地理轮廓')
        template=template.replace('连线仅表示城市间的旅行顺序，不代表实际道路或精确地理位置。交通方式与返程线路待确认。','主要游玩地区放大展示；抵达与离开放在小图。城市按经纬度定位，连线表示旅行顺序，不代表精确道路或航迹。')
    renderer=(ROOT/'assets'/'segment-animation.js').read_text(encoding='utf-8')
    template=re.sub(r'function setTravelerAt\(.*?\n    const routePreview',lambda _:renderer+'\n    const routePreview',template,count=1,flags=re.S)
    template=template.replace("[...routeMap.querySelectorAll('.route-leg')]", "[...routeMap.querySelectorAll('.route-leg')].sort((a,b)=>Number(a.dataset.leg)-Number(b.dataset.leg))")
    if data['duration']<=4:
        template=template.replace('<div class="route-grid">','<div class="route-grid short-itinerary'+(' odd-short' if data['duration']%2 else '')+'" style="--short-days:'+str(data['duration'])+'">')
    template=re.sub(r'<button class="route-preview-close".*?</button>','',template,count=1,flags=re.S)
    template=template.replace("document.getElementById('route-preview-close').addEventListener", "document.getElementById('route-preview-close')?.addEventListener")
    template=template.replace("button.setAttribute('aria-controls','route-preview');", "button.setAttribute('aria-controls','route-preview');button.setAttribute('aria-label',trip[index].date+' · '+trip[index].subtitle+' · '+(!routePreview.hidden&&index===day?'收起预览':'展开预览'));")
    external='<svg class="ui-icon" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true"><path d="M7 17 17 7M7 7h10v10"/></svg>'
    template=template.replace('导航 ↗</a>','<span>导航</span>'+external+'</a>')
    template=template.replace('>保存行程页</a>','><span>保存行程页</span><svg class="ui-icon" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8" aria-hidden="true"><path d="M12 3v12m-4-4 4 4 4-4M5 16v5h14v-5"/></svg></a>')
    template=template.replace('function showDay(i,changeHash=true){','function showDay(i,changeHash=true,pinArea=true){').replace('const pinnedTop=before.top<0','const pinnedTop=pinArea&&before.top<0')
    template=template.replace('showDay(next);openRoutePreview(next)', 'showDay(next,true,false);openRoutePreview(next)')
    template=template.replace('function playRoute(){', 'function playRoute(){if(!routeLegs.length)return;')
    saver=(ROOT/'assets'/'offline-save.js').read_text(encoding='utf-8')
    template=re.sub(r"    document.getElementById\('download'\).addEventListener\('click'.*?;\n    showDay",lambda _:saver+'\n    showDay',template,count=1,flags=re.S)
    template=template.replace("document.getElementById('focus-link').textContent=activeDay===0?'查看交通与住宿 ↓':'查看这一天的安排 ↓';", "document.getElementById('focus-link').innerHTML='<span>'+(activeDay===0?'查看交通与住宿':'查看这一天的安排')+'</span><svg class=\"ui-icon\" viewBox=\"0 0 24 24\" fill=\"none\" stroke=\"currentColor\" stroke-width=\"1.8\" aria-hidden=\"true\"><path d=\"m6 9 6 6 6-6\"/></svg>';")
    motion=(ROOT/'assets'/'day-motion.js').read_text(encoding='utf-8')
    template=re.sub(r'    function prepareDayMotion\(targets\)\{.*?(?=    function closeRoutePreview)',lambda _:motion,template,count=1,flags=re.S)
    preview_summary='<div class="route-preview-summary" id="route-preview-summary"></div>'
    template=template.replace('<ol class="route-preview-list"',preview_summary+'<ol class="route-preview-list"',1)
    template=template.replace("document.getElementById('route-preview-path').textContent=d.subtitle;","document.getElementById('route-preview-path').textContent=d.subtitle;document.getElementById('route-preview-title').textContent=d.previewTitle;document.getElementById('route-preview-summary').innerHTML=d.previewIconSvg+'<span>'+esc(d.previewSummary)+'</span>';",1)
    from theme_tokens import tokens
    # Destination decoration precedes the fixed component geometry and paint contract.
    stylesheet=data.get('visualTheme',{}).get('stylesheet')
    if stylesheet:
        path=(directory/stylesheet).resolve()
        if directory.resolve() not in path.parents:raise ValueError('Theme stylesheet must be inside project directory')
        css=path.read_text(encoding='utf-8')
        if re.search(r'</style',css,re.I):raise ValueError('Theme stylesheet must not contain a closing style tag')
        template=template.replace('</head>','<style id="destination-theme">'+css+'</style></head>')
    styles=tokens(data)+(ROOT/'assets'/'components.css').read_text(encoding='utf-8')+(ROOT/'assets'/'desktop-navigation.css').read_text(encoding='utf-8')+(ROOT/'assets'/'tablet-and-motion.css').read_text(encoding='utf-8')+(ROOT/'assets'/'orders.css').read_text(encoding='utf-8')+(ROOT/'assets'/'map-navigation.css').read_text(encoding='utf-8')+(ROOT/'assets'/'control-theme.css').read_text(encoding='utf-8')
    template=template.replace('</head>','<style id="roadbook-components">'+styles+'</style></head>')
    template=re.sub(r'<meta name="theme-color" content="[^"]*">','<meta name="theme-color" content="'+colors['bg']+'">',template,count=1)
    from urllib.parse import quote
    favicon='<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 64 64"><rect width="64" height="64" rx="14" fill="'+colors['surface']+'"/><path d="M8 47 24 22l10 15 8-10 14 20Z" fill="'+colors['accent']+'"/></svg>'
    template=re.sub(r'<link rel="icon"[^>]*>','<link rel="icon" type="image/svg+xml" href="data:image/svg+xml,'+quote(favicon)+'">',template,count=1)
    nav=(ROOT/'assets'/'desktop-navigation.html').read_text(encoding='utf-8')
    script=(ROOT/'assets'/'desktop-navigation.js').read_text(encoding='utf-8')
    template=template.replace('</body>',nav+'<script>'+script+'</script></body>')
    assert not remainders(template), remainders(template)
    Path(output).parent.mkdir(parents=True,exist_ok=True)
    Path(output).write_text(template,encoding='utf-8')


def remainders(template):
    import re
    return re.findall(r'__(?:IMG|ROUTE|BOOKING|CONFIG|DAY|TODO|TIPS|BRAND|PERIOD|ORIGIN|INTRO|TITLE|FOOD|DISCLAIMER|MAP)[A-Z_]*__',template)


if __name__=='__main__':
    path=Path(sys.argv[1]);build(json.loads(path.read_text(encoding='utf-8-sig')),sys.argv[2],path.parent)
