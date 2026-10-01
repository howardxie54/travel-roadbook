"""Optional destination presentation layer; preserve core roadbook interactions."""
import html
import re
from pathlib import Path
from geographic_map import map_svg


def apply_design(page,data,directory,embed):
    root=Path(__file__).resolve().parent.parent
    if data.get('destinationTheme')!='thailand-summer':return page
    title=html.escape(data.get('displayTitle') or data.get('visualLine') or '泰国的夏天')
    cities=' / '.join(c['label'] for c in data.get('geographicMap',{}).get('cities',[]) if c.get('country')=='TH') or '泰国旅行'
    hero='<section class="intro destination-hero" aria-labelledby="page-title"><div class="hero-kicker">THAILAND / '+html.escape(cities)+'</div><h1 id="page-title">'+title+'<span class="hero-subline">'+html.escape(data.get('heroSubline','在城市与海风之间'))+'</span></h1><p>'+html.escape(data['subtitle'])+'</p><div class="trip-seal"><b>'+str(data['duration'])+' DAYS</b><span>'+html.escape(data['origin']+'出发 · '+(data.get('dates') or '日期待定'))+'</span></div><div class="hero-sun" aria-hidden="true"></div><div class="hero-waves" aria-hidden="true"></div></section>'
    page=re.sub(r'<section class="intro".*?</section>',lambda _:hero,page,count=1,flags=re.S)
    # Remove the original word-by-word artwork animation, retaining preview motion separately.
    page=re.sub(r'<script>\s*\(\(\)=>\{\s*const reduce=matchMedia.*?</script>','',page,count=1,flags=re.S)
    atlas=embed(data['transportAtlas'],directory) if data.get('transportAtlas') else ''
    if data.get('geographicMap',{}).get('cities'):
        map_markup=map_svg(data,directory,atlas)
        page=re.sub(r'<svg class="route-map".*?</svg>',lambda _:map_markup,page,count=1,flags=re.S)
    page=page.replace('<div class="route-grid">','<div class="route-grid'+(' long-itinerary' if data['duration']>4 else '')+'">')
    css=(root/'assets'/'thailand.css').read_text(encoding='utf-8')
    page=page.replace('</head>','<style>'+css+'</style></head>')
    if data.get('geographicMap',{}).get('cities'):
        page=page.replace('路线示意 · 交通待确认','主要游玩地区 · 经纬度定位')
        page=page.replace('示意图 · 非地理底图','© OpenStreetMap contributors · 离线地理轮廓：Natural Earth')
        page=page.replace('连线仅表示城市间的旅行顺序，不代表实际道路或精确地理位置。交通方式与返程线路待确认。','大图展示主要游玩地区，抵达与离开放在小图。城市按经纬度定位；连线表示旅行顺序，不代表实际道路或航迹。待定区段沿用已知交通插画，实际方式仍待确认。')
    traveler=(root/'assets'/'segment-animation.js').read_text(encoding='utf-8')
    page=re.sub(r'function setTravelerAt\(.*?\n    const routePreview',lambda _:traveler+'\n    const routePreview',page,count=1,flags=re.S)
    page=page.replace('<div class="route-grid','<p class="transport-note">'+html.escape(data.get('transportNote','按行程自动切换交通；待定区段沿用已知插画，实际方式仍待确认。'))+'</p><div class="route-grid',1)
    # Move the single preview below the selected row, not below the last day.
    page=page.replace('function renderRoutePreview(day){const d=trip[day]',"function renderRoutePreview(day){if(config.longItinerary){const row=routeCards[day];row.insertAdjacentElement('afterend',routePreview)}const d=trip[day]")
    extra="""<script>
(()=>{
const track=document.querySelector('.daynav .shell');
function revealTab(){const active=track.querySelector('[aria-selected="true"]');if(!active)return;const a=active.getBoundingClientRect(),b=track.getBoundingClientRect();if(a.left<b.left+10||a.right>b.right-10)track.scrollLeft+=a.left-b.left-(b.width-a.width)/2}
new MutationObserver(revealTab).observe(track,{subtree:true,attributes:true,attributeFilter:['aria-selected']});
const list=document.querySelector('.route-grid');function revealRoute(){const active=list.querySelector('[aria-pressed="true"]');if(!active)return;const a=active.getBoundingClientRect(),b=list.getBoundingClientRect();if(a.top<b.top||a.bottom>b.bottom)list.scrollTop+=a.top-b.top-(b.height-a.height)/2}new MutationObserver(revealRoute).observe(list,{subtree:true,attributes:true,attributeFilter:['aria-pressed']});
const reduce=matchMedia('(prefers-reduced-motion: reduce)'),preview=document.getElementById('route-preview');new MutationObserver(()=>{if(!preview.hidden&&!reduce.matches)preview.animate([{opacity:.4,transform:'translateY(-6px)'},{opacity:1,transform:'none'}],{duration:220,easing:'ease-out'})}).observe(preview,{attributes:true,attributeFilter:['hidden']});
})();</script>"""
    return page.replace('</body>',extra+'</body>')
