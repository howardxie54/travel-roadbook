"""Validate reusable place bindings; keep unverified data as search-only."""
import copy,math
from urllib.parse import urlparse

def map_url_allowed(value,provider):
    if not isinstance(value,str):return False
    try:
        u=urlparse(value)
        port=u.port
    except ValueError:return False
    if u.scheme!='https' or u.username or u.password or port not in (None,443):return False
    if provider=='amap':return u.hostname in ('uri.amap.com','surl.amap.com')
    return (u.hostname=='www.google.com' and u.path.startswith('/maps')) or u.hostname in ('maps.google.com','maps.app.goo.gl') or (u.hostname=='goo.gl' and u.path.startswith('/maps/'))

def normalize_places(records,pending):
    result=[];keys=set()
    for raw in records or []:
        p=copy.deepcopy(raw)
        if not isinstance(p.get('key'),str) or not p['key'].strip() or p['key'] in keys:raise ValueError('Map place keys must be present and unique')
        keys.add(p['key'])
        if p.get('provider') not in ('amap','google') or not all(isinstance(p.get(k),str) and p[k].strip() for k in ('name','city')):raise ValueError('Map places require provider, name and single city')
        if any(s in p['city'] for s in ('→','->',' / ','、')):raise ValueError('Map place city must be a single city')
        coords=p.get('coordinates')
        if coords:
            for k,limit in [('lat',90),('lon',180)]:
                v=coords.get(k)
                if isinstance(v,bool) or not isinstance(v,(int,float)) or not math.isfinite(v) or not -limit<=v<=limit:raise ValueError('Map place coordinates must be finite and in range')
            if coords.get('crs') not in ('wgs84','gcj02'):raise ValueError('Map place coordinate system is required')
        if p.get('shareUrl') and not map_url_allowed(p['shareUrl'],p['provider']):
            p.pop('shareUrl');pending.append(p['name']+'：地图分享链接与服务不符，暂不使用该链接。')
        if p.get('placeId') and (not isinstance(p['placeId'],str) or not p['placeId'].strip() or len(p['placeId'])>256):raise ValueError('Map place ID must be a nonempty string of at most 256 characters')
        p['verified']=p.get('verified') is True and bool(p.get('checkedAt') and p.get('source')) and not p.get('synthetic')
        if not p['verified']:pending.append(p['name']+'：地图记录待核对，暂提供名称查找。')
        p.setdefault('aliases',[])
        if not isinstance(p['aliases'],list) or not all(isinstance(a,str) for a in p['aliases']):raise ValueError('Map aliases must be a list of strings')
        result.append(p)
    return result
