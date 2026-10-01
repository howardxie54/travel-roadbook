"""Accept sparse assistant-authored trip data; keep unknown facts visibly unknown."""
import copy
from datetime import datetime

ALIASES={'飞机':'plane','火车':'train','高铁':'train','汽车':'car','自驾':'car','自行车':'bike'}
def known(value):return bool(value and not any(word in str(value) for word in ('待补充','待确认','待定','待订','待提供','未提供','未知','虚构')))
def normalize(raw):
    d=copy.deepcopy(raw)
    duration=d.get('duration',len(d.get('days') or []))
    if isinstance(duration,bool) or not isinstance(duration,int) or not 1<=duration<=90:raise ValueError('duration must be an integer from 1 to 90')
    d['duration']=duration
    destinations=d.get('destinations') or []
    d.setdefault('title','与'.join(destinations) if destinations else '旅行路书')
    d.setdefault('origin','出发地待补充');d.setdefault('subtitle','先把计划放进路书，再逐步补齐安排。')
    for key in ('bookings','conflicts','pending','transports','countdowns','routeSegments','tickets','groundOrders','otherOrders'):
        if d.get(key) is None:d[key]=[]
    if not d.get('theme'):d['theme']={}
    d['theme'].setdefault('large',False)
    if d.get('visualTheme') is None:d['visualTheme']={}
    if d.get('geographicMap') is None:d['geographicMap']={}
    if d.get('foodImages') is None:d['foodImages']={}
    if d.get('mapProviders') is None:d['mapProviders']={}
    if d.get('days') is None:d.pop('days',None)
    d.setdefault('days',[dict(city=destinations[0] if len(destinations)==1 else '城市待分配') for _ in range(duration)])
    if len(d['days'])!=duration:raise ValueError('days length must match duration; do not silently delete or invent extra travel days')
    for n,day in enumerate(d['days'],1):
        day.setdefault('id','day-'+str(n));day.setdefault('number',n);day.setdefault('city','城市待分配');day.setdefault('status','暂定');day.setdefault('summary','当天内容尚可继续补充。')
        if day['number']!=n:raise ValueError('day numbers must follow the itinerary order')
        if not day.get('events'):day['events']=[dict(title='当天安排待补充',detail='补充活动、酒店或交通后更新。',status='待补充')]
        for i,event in enumerate(day['events'],1):
            event.setdefault('id',day['id']+'-event-'+str(i));event.setdefault('title','安排待补充');event.setdefault('detail','具体信息待补充。');event.setdefault('status','待补充')
            navigation_city=event.get('city') or day.get('navigationCity') or day['city']
            if event.get('place') and any(s in navigation_city for s in ('→','->',' / ','、')):
                event['_navigationPending']=True
                d['pending'].append('第 '+str(n)+' 天 · '+event['title']+'：请补充地点所属城市后启用导航。')
            else:event.setdefault('city',navigation_city)
        for food in day.get('food') or []:
            for key,value in [('title','餐饮待补充'),('kind','推荐待核实'),('image','placeholder'),('desc','补充偏好与资料后再确认推荐。')]:food.setdefault(key,value)
            food.setdefault('city',day.get('navigationCity') or day['city'])
            if food.get('address') and any(s in food['city'] for s in ('→','->',' / ','、')):
                food['_navigationPending']=True
                d['pending'].append('第 '+str(n)+' 天 · '+food['title']+'：请补充餐饮地点所属城市后启用导航。')
    ids=[day['id'] for day in d['days']]+[event['id'] for day in d['days'] for event in day['events']]
    if len(set(ids))!=len(ids):raise ValueError('day and event IDs must be unique')
    for n,b in enumerate(d['bookings'],1):
        b.setdefault('id','stay-'+str(n));b.setdefault('city','城市待补充');b.setdefault('name','住宿名称待补充');b.setdefault('address','地址待补充');b.setdefault('nights',[]);b.setdefault('status','待补充');b.setdefault('synthetic',False)
        b['_canNavigate']=not b['synthetic'] and known(b['name']) and known(b['city'])
        if b.get('nights') is None:b['nights']=[]
    for key,prefix in [('transports','transport'),('tickets','ticket'),('groundOrders','ground'),('otherOrders','order')]:
        for n,record in enumerate(d[key],1):
            record.setdefault('id',prefix+'-'+str(n));record.setdefault('status','待补充')
            if key=='transports':
                record.setdefault('mode','unknown');record.setdefault('from','出发地待补充');record.setdefault('to','目的地待补充')
    from order_sections import state
    for hotel in d['bookings']:
        if state(hotel) in ('cancelled','not_needed'):continue
        for night in hotel['nights']:
            if not isinstance(night,int) or isinstance(night,bool) or not 1<=night<=duration:
                d['pending'].append(hotel['name']+'：入住晚数与当前旅行天数需要核对，原订单已保留。')
                continue
            overnight=d['days'][night-1].get('overnightCity')
            if state(hotel)=='confirmed' and known(overnight) and known(hotel['city']) and overnight!=hotel['city']:
                d['conflicts'].append('第 '+str(night)+' 晚计划在'+overnight+'，已订住宿在'+hotel['city']+'；请确认往返或改订，原预订未取消。')
    all_ids=ids+[record['id'] for key in ('bookings','transports','tickets','groundOrders','otherOrders') for record in d[key]]
    if len(set(all_ids))!=len(all_ids):raise ValueError('day, event and order IDs must be unique')
    for segment in d.get('routeSegments',[]):segment['mode']=ALIASES.get(segment.get('mode'),segment.get('mode','unknown'))
    valid_countdowns=[]
    for countdown in d['countdowns']:
        if not countdown.get('at'):
            d['pending'].append(countdown.get('title','旅行倒计时')+'：时间待补充，未启动倒计时。')
            continue
        try:at=datetime.fromisoformat(str(countdown['at']).replace('Z','+00:00'))
        except (ValueError,TypeError):raise ValueError('countdown at must be a valid ISO timestamp with timezone')
        if at.tzinfo is None:raise ValueError('countdown timezone is required')
        countdown.setdefault('title','旅行倒计时');countdown.setdefault('note','')
        valid_countdowns.append(countdown)
    d['countdowns']=valid_countdowns
    providers={c['label']:('amap' if c.get('country')=='CN' else 'google') for c in d.get('geographicMap',{}).get('cities',[]) if c.get('country')}
    providers.update(d.get('mapProviders',{}));d['mapProviders']=providers
    from navigation_places import normalize_places
    d['mapPlaces']=normalize_places(d.get('mapPlaces'),d['pending'])
    return d
