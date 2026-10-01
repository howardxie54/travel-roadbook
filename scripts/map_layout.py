"""Reusable destination-first map. No country-specific coordinate assertions."""
import html
import math
from pathlib import Path
from geographic_map import layer,world

ROOT=Path(__file__).resolve().parent.parent
esc=lambda value:html.escape(str(value),quote=True)


def fit_bounds(cities,padding=.28,minimum=.65):
    angles=sorted((float(c['lon'])+360)%360 for c in cities)
    gaps=[(angles[(i+1)%len(angles)]-a)%360 for i,a in enumerate(angles)]
    start=angles[(gaps.index(max(gaps))+1)%len(angles)] if len(angles)>1 else angles[0]
    lons=[start+(a-start)%360 for a in angles]
    centre=(min(lons)+max(lons))/2
    while centre>180:centre-=360;lons=[a-360 for a in lons]
    lats=[float(c['lat']) for c in cities]
    dx=max(minimum,max(lons)-min(lons));dy=max(minimum,max(lats)-min(lats))
    cy=(min(lats)+max(lats))/2
    return [centre-dx*(.5+padding),max(-84,cy-dy*(.5+padding)),centre+dx*(.5+padding),min(84,cy+dy*(.5+padding))]


def zoom_for(bounds,width):
    span=max(.1,bounds[2]-bounds[0]);return max(1,min(9,int(math.log2(width*360/(256*span)))))


def plan(data):
    cfg=data['geographicMap'];cities=cfg['cities']
    if not cities:raise ValueError('A map needs at least one verified city coordinate')
    for c in cities:
        if not all(isinstance(c.get(k),(int,float)) and not isinstance(c[k],bool) and math.isfinite(c[k]) for k in ('lon','lat')) or not -180<=c['lon']<=180 or not -85<=c['lat']<=85:raise ValueError('Invalid coordinate: '+str(c.get('label','')))
    primary=cfg.get('focusCountry',data.get('country'))
    focus=cfg.get('focusIndices')
    if focus is None:
        focus=[i for i,c in enumerate(cities) if i>0 and c.get('role') not in ('origin','exit') and (not primary or not c.get('country') or c['country']==primary)]
    if not focus:focus=list(range(1,len(cities))) or [0]
    if any(not isinstance(i,int) or i<0 or i>=len(cities) for i in focus):raise ValueError('Invalid focusIndices')
    if len(cities)==1:return cities,focus,[]
    lookup={str(c.get('id',i)):i for i,c in enumerate(cities)}
    lookup.update({c['label']:i for i,c in enumerate(cities)})
    entries=data.get('routeSegments') or [{} for _ in cities[1:]]
    legs=[]
    for i,entry in enumerate(entries):
        for endpoint in ('from','to'):
            if entry.get(endpoint) is not None and str(entry[endpoint]) not in lookup:raise ValueError('Route endpoint missing from verified cities: '+str(entry[endpoint]))
        a=lookup.get(str(entry.get('from')),min(i,len(cities)-2))
        b=lookup.get(str(entry.get('to')),min(i+1,len(cities)-1))
        if a==b:continue
        legs.append(dict(index=i,a=a,b=b,view='focus' if a in focus and b in focus else 'overview'))
    return cities,focus,legs


def render_map(data,directory,atlas_image=''):
    cfg=data['geographicMap'];cities,focus,legs=plan(data)
    land=directory/cfg['landAsset'] if cfg.get('landAsset') else ROOT/'assets/world-land.geojson'
    if not land.exists():land=ROOT/'assets/world-land.geojson'
    online=cfg.get('onlineTiles',True)
    focus_bounds=cfg.get('focusBounds') or fit_bounds([cities[i] for i in focus])
    overview_bounds=cfg.get('overviewBounds') or fit_bounds(cities,padding=.15,minimum=1)
    road=directory/cfg['roadsAsset'] if cfg.get('roadsAsset') else None
    base,focus_points=layer(focus_bounds,600,545,zoom_for(focus_bounds,600),land,cities,road,online)
    overview,overview_points=layer(overview_bounds,205,150,zoom_for(overview_bounds,205),land,cities,None,online)
    if not atlas_image:
        import base64
        atlas_image='data:image/svg+xml;base64,'+base64.b64encode((ROOT/'assets/transport-fallback.svg').read_bytes()).decode()

    def route_paths(view,points):
        output=[]
        for leg in legs:
            if leg['view']!=view:continue
            a,b=points[leg['a']],points[leg['b']]
            d='M{} {} L{} {}'.format(a['x'],a['y'],b['x'],b['y'])
            # International line is a travel connector, not a claim about a flown route.
            if view=='overview':d='M{} {} Q{} {} {} {}'.format(a['x'],a['y'],(a['x']+b['x'])/2-7,(a['y']+b['y'])/2-14,b['x'],b['y'])
            output.append('<path class="route-leg" data-leg="'+str(leg['index'])+'" data-map-view="'+view+'" data-from="'+esc(cities[leg['a']]['label'])+'" data-to="'+esc(cities[leg['b']]['label'])+'" d="'+d+'" style="stroke-width:'+('3' if view=='overview' else '5')+'"/>')
        return ''.join(output)

    def labels(points,indices,small=False):
        out=[];placed=[]
        for index in indices:
            c=points[index];x,y=c['x'],c['y'];size=9 if small else 17
            c=dict(c,label=str(focus.index(index)+1)) if not small and len(focus)>6 else c
            tx=max(8,min((205 if small else 600)-len(c['label'])*size-8,x+10));ty=y-12 if y>35 else y+24
            for px,py in placed:
                if abs(tx-px)<len(c['label'])*size and abs(ty-py)<size+6:ty+=size+10
            placed.append((tx,ty))
            out.append('<circle cx="'+str(x)+'" cy="'+str(y)+'" r="'+('3' if small else '6')+'" fill="#a56d26" stroke="#fff9ed" stroke-width="2"/><text x="'+str(tx)+'" y="'+str(ty)+'" font-size="'+str(size)+'" fill="#513d23" stroke="#fffdf4" stroke-width="'+('2.5' if small else '5')+'" paint-order="stroke" font-weight="700">'+esc(c['label'])+'</text>')
        return ''.join(out)

    def traveler(small=False):
        prefix='' if small else 'local-';tid='route-traveler' if small else 'local-traveler';hid='route-heading' if small else 'local-heading';sid='cat-sprite' if small else 'local-cat-sprite';size=42 if small else 92
        return '<g id="'+tid+'"><g id="'+hid+'"><svg id="'+sid+'" x="-'+str(size/2)+'" y="-'+str(size/2)+'" width="'+str(size)+'" height="'+str(size)+'" viewBox="0 0 512 512" overflow="hidden"><use href="#transport-atlas-image"/></svg></g></g>'

    # Keep the small arrival/departure overview away from destination labels.
    candidates=[(360,15),(15,15),(360,355),(15,355)]
    corner=min(candidates,key=lambda xy:sum(xy[0]-65<p['x']<xy[0]+290 and xy[1]-65<p['y']<xy[1]+245 for i,p in enumerate(focus_points) if i in focus))
    origin_title=cfg.get('overviewLabel','抵达与离开')
    inset='<svg id="arrival-map" data-map-role="overview" x="'+str(corner[0])+'" y="'+str(corner[1])+'" width="225" height="183" viewBox="0 0 225 183"><rect width="225" height="183" rx="14" fill="#fffdf5" stroke="#ddc696"/><text x="12" y="20" font-size="12" fill="#6d522c">'+esc(origin_title)+'</text><svg x="10" y="27" width="205" height="150" viewBox="0 0 205 150" overflow="hidden">'+overview+route_paths('overview',overview_points)+traveler(True)+labels(overview_points,list(dict.fromkeys([leg['a'] for leg in legs if leg['view']=='overview']+[leg['b'] for leg in legs if leg['view']=='overview'])),True)+'</svg></svg>'
    focus_title=cfg.get('focusLabel','主要游玩区域')
    if not any(leg['view']=='overview' for leg in legs):inset=''
    # Each scene uses its own consistent projection; never stretch the departure point into the focus view.
    markup='<svg class="route-map" id="route-map" data-focus-cities="'+esc('|'.join(cities[i]['label'] for i in focus))+'" viewBox="0 0 600 545" role="img" aria-label="'+esc(focus_title+'，含抵达与离开概览')+'"><defs><image id="transport-atlas-image" href="'+atlas_image+'" width="1024" height="1024"/><clipPath id="focus-frame"><rect width="600" height="545"/></clipPath></defs><path id="route-loop" d="M0 0L1 1" fill="none" stroke="none"/><svg id="local-map" data-map-role="focus" width="600" height="545" viewBox="0 0 600 545" overflow="hidden"><g clip-path="url(#focus-frame)">'+base+'</g>'+route_paths('focus',focus_points)+traveler()+labels(focus_points,focus)+'<g><rect x="14" y="15" width="48" height="28" rx="8" fill="#fffdf3"/><text x="38" y="35" text-anchor="middle" font-size="15" fill="#604826">N ↑</text></g></svg>'+inset+'</svg>'

    if len(focus)>6:
        markup+='<ol class="map-legend">'+''.join('<li><b>'+str(n+1)+'</b>'+esc(cities[i]['label'])+'</li>' for n,i in enumerate(focus))+'</ol>'
    return markup
