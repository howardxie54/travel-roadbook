"""Coordinate-projected map with online OSM tiles and offline land fallback."""
import html
import json
import math
from pathlib import Path

def world(lon, lat, zoom):
    size=256*2**zoom
    lat=max(-85,min(85,lat))
    rad=math.radians(lat)
    return (lon+180)/360*size,(1-math.asinh(math.tan(rad))/math.pi)/2*size


def layer(bounds, width, height, zoom, country_file, cities,roads_file=None,online=True):
    west,south,east,north=bounds
    x0,y0=world(west,north,zoom);x1,y1=world(east,south,zoom)
    scale=min(width/(x1-x0),height/(y1-y0))
    ox=(width-(x1-x0)*scale)/2;oy=(height-(y1-y0)*scale)/2
    def project(lon,lat):
        centre=(west+east)/2
        lon=centre+(lon-centre+180)%360-180
        x,y=world(lon,lat,zoom)
        return round(ox+(x-x0)*scale,2),round(oy+(y-y0)*scale,2)
    parts=['<rect width="'+str(width)+'" height="'+str(height)+'" fill="#cde8ed"/>']
    if country_file and Path(country_file).exists():
        geo=json.loads(Path(country_file).read_text(encoding='utf-8'))
        for f in geo['features']:
            polygons=f['geometry']['coordinates'] if f['geometry']['type']=='MultiPolygon' else [f['geometry']['coordinates']]
            for poly in polygons:
                ring=poly[0]
                lons=[(west+east)/2+(p[0]-(west+east)/2+180)%360-180 for p in ring]
                lats=[p[1] for p in ring]
                if max(lons)<west or min(lons)>east or max(lats)<south or min(lats)>north:continue
                path='M'+' L'.join(' '.join(map(str,project(lon,lat))) for lon,lat,*rest in ring)+'Z'
                parts.append('<path d="'+path+'" fill="#f9f2db" stroke="#c8bc9a" stroke-width="1"/>')
    # Loaded only for the visible map, as normal online map display. No offline tile prefetch.
    for x in range(math.floor(x0/256),math.floor(x1/256)+1) if online else []:
        for y in range(math.floor(y0/256),math.floor(y1/256)+1):
            parts.append('<image class="online-map-tile" href="https://tile.openstreetmap.org/{}/{}/{}.png" x="{}" y="{}" width="{}" height="{}"/>'.format(zoom,x%(2**zoom),max(0,min(2**zoom-1,y)),round(ox+(x*256-x0)*scale,2),round(oy+(y*256-y0)*scale,2),round(256*scale+.2,2),round(256*scale+.2,2)))
    if roads_file and Path(roads_file).exists():
        roads=json.loads(Path(roads_file).read_text(encoding='utf-8'))
        for road in roads['elements']:
            coordinates=road.get('geometry',[])
            if not coordinates:continue
            path='M'+' L'.join(' '.join(map(str,project(c['lon'],c['lat']))) for c in coordinates)
            parts.append('<path d="'+path+'" fill="none" stroke="#fffdf3" stroke-width="3"/><path d="'+path+'" fill="none" stroke="#d6af68" stroke-width="1.2"/>')
    return ''.join(parts),[dict(c,x=project(c['lon'],c['lat'])[0],y=project(c['lon'],c['lat'])[1]) for c in cities]


def map_svg(data,directory,atlas_image=''):
    from map_layout import render_map
    return render_map(data,directory,atlas_image)
