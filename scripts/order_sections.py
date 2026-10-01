"""Render supplied reservations faithfully; never invent bookings or conditions."""
import html
import re

def esc(value):return html.escape(str(value),quote=True)
MODES={'plane':'飞机','train':'火车 / 高铁','car':'汽车','bike':'自行车','unknown':'方式待确认'}

def state(record):
    explicit=record.get('bookingState')
    if explicit in ('confirmed','pending_payment','planned','unknown','cancelled','not_needed'):return explicit
    text=str(record.get('status') or '')
    if record.get('synthetic'):return 'unknown'
    if any(w in text for w in ('已取消','取消成功')):return 'cancelled'
    if any(w in text for w in ('待付款','未付款')):return 'pending_payment'
    if any(w in text for w in ('未订','待订','偏好','计划','暂定')):return 'planned'
    if any(w in text for w in ('待确认','取消中','未取消')):return 'unknown'
    if any(w in text for w in ('已订','已确认','已出票','预订成功')):return 'confirmed'
    return 'unknown'

def badge(record):
    labels={'confirmed':'已确认','pending_payment':'待付款','planned':'计划 / 待订','unknown':'待补充','cancelled':'已取消','not_needed':'不需要'}
    return '<span class="order-state" data-order-state="'+state(record)+'">'+('虚构测试' if record.get('synthetic') else labels[state(record)])+'</span>'

def rows(record,fields,private=False):
    result=[]
    for key,label in fields:
        value=record.get(key)
        if value is None or value=='' or value==[]:continue
        if isinstance(value,list):value='、'.join(map(str,value))
        result.append('<div><dt>'+esc(label)+'</dt><dd>'+esc(value)+'</dd></div>')
    if private and record.get('bookingReference'):result.append('<div><dt>预订参考号 · 私人版</dt><dd>'+esc(record['bookingReference'])+'</dd></div>')
    return '<dl class="order-fields">'+''.join(result)+'</dl>' if result else ''

def more(record,fields,private=False):
    details=rows(record,fields,private)
    url=record.get('officialUrl') or record.get('url')
    if isinstance(url,str) and re.match(r'^https?://',url,re.I):details+='<a class="btn alt" href="'+esc(url)+'" target="_blank" rel="noopener noreferrer">官方资料 / 预订入口</a>'
    if not details:return ''
    return '<details class="order-more"><summary>查看订单信息<svg class="ui-icon" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.7" aria-hidden="true"><path d="m6 9 6 6 6-6"/></svg></summary>'+details+'</details>'

def group(kind,title,items,empty):
    return '<section class="booking-item order-group" data-order-category="'+kind+'"><h3>'+title+'</h3>'+(''.join(items) or '<p class="order-empty">'+empty+'</p>')+'</section>'

def render(data,segments):
    private=bool(data.get('includePrivateOrders')) and data.get('shareMode')!='public'
    transport_fields=[('date','出发日期'),('timezone','时区'),('arrivalDate','到达日期'),('arrivalTimezone','到达时区'),('carrier','航司 / 运营方'),('number','航班 / 车次'),('departurePlace','出发机场 / 车站'),('departureTerminal','出发航站楼'),('arrivalPlace','到达机场 / 车站'),('arrivalTerminal','到达航站楼'),('seatClass','舱位 / 席别'),('baggage','行李规则'),('checkInDeadline','办理截止'),('price','已提供的金额'),('currency','币种'),('paymentStatus','付款状态'),('cancellation','用户提供的退改规则'),('note','备注')]
    transport=[]
    for t in data['transports']:
        mode=MODES.get(t.get('mode'),t.get('mode') or '交通')
        transport.append('<article class="flight-card order-entry" data-order-id="'+esc(t['id'])+'"><div class="order-entry-head"><b>'+esc(mode)+'</b>'+badge(t)+'</div><div class="order-route">'+esc(t['from'])+' → '+esc(t['to'])+'</div><p class="order-time">'+esc(t.get('departure') or '出发时刻待补充')+' → '+esc(t.get('arrival') or '到达时刻待补充')+'</p><p>'+esc(t['status'])+'</p>'+more(t,transport_fields,private)+'</article>')
    summary='；'.join(MODES.get(t.get('mode'),t.get('mode') or '方式待确认')+' · '+t.get('from','出发地待定')+' → '+t.get('to','目的地待定')+'（'+t.get('status','班次与预订待补充')+'）' for t in segments)
    traffic=group('transport','交通与航班',transport,'交通班次待补充；已知出行方式可先保留为计划，不代表已出票。')
    if summary:traffic=traffic.replace('</section>','<div class="booking-row"><span>路线交通计划</span><b>'+esc(summary)+'</b></div></section>')
    meeting=data.get('meeting') or {}
    traffic=traffic.replace('</section>','<div class="order-meeting"><b>集合与衔接</b>'+ (rows(meeting,[('time','集合时间'),('timezone','时区'),('place','集合地点'),('group','同行小组'),('note','衔接说明')]) or '<p>集合时间、地点和机场 / 车站接驳待补充。</p>')+'</div></section>')
    hotel_fields=[('checkIn','入住日期'),('checkOut','退房日期'),('timezone','时区'),('roomType','房型'),('rooms','房间数'),('guests','入住人数'),('breakfast','早餐'),('checkInTime','办理入住时间'),('price','已提供的金额'),('currency','币种'),('paymentStatus','付款状态'),('cancellation','用户提供的退改规则'),('contact','酒店公开联系方式'),('note','备注')]
    hotels=[]
    for b in data['bookings']:
        night='第 '+'、'.join(map(str,b['nights']))+' 晚' if b['nights'] else '入住晚数待补充'
        hotels.append('<article class="hotel-row order-entry" data-order-id="'+esc(b['id'])+'"'+(' data-map-city="'+esc(b['city'])+'" data-map-query="'+esc(b.get('mapQuery') or b['name'])+'" data-map-key="'+esc(b.get('mapPlaceKey',''))+'"' if b['_canNavigate'] else '')+'><div class="hotel-info"><div class="order-entry-head"><span class="hotel-date">'+esc(night)+' · '+esc(b['city'])+'</span>'+badge(b)+'</div><h4 class="hotel-name">'+esc(b['name'])+'</h4><p class="hotel-address">'+esc(b['address'])+'</p><p class="hotel-note">'+esc(b['status'])+(' · 虚构测试，不提供导航' if b['synthetic'] else '')+'</p>'+more(b,hotel_fields,private)+'</div>'+('<div class="hotel-action"><a class="hotel-map-link" target="_blank" rel="noopener noreferrer"><span>导航</span><svg class="ui-icon" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.7" aria-hidden="true"><path d="M7 17 17 7M7 7h10v10"/></svg></a></div>' if b['_canNavigate'] else '')+'</article>')
    stays=group('stay','住宿安排',hotels,'住宿待补充 · 名称、城市、入住日期 / 晚数和地址确认后更新；不生成虚构导航。')
    extra_fields=[('city','所在城市'),('date','使用日期'),('time','预约时段'),('timezone','时区'),('place','入口 / 集合点'),('quantity','人数 / 数量'),('pickup','取车 / 接送地点'),('pickupAt','取车 / 接送时间'),('returnPlace','归还地点'),('returnAt','归还时间'),('provider','服务方'),('coverage','用户提供的保障范围'),('validFrom','起始日期'),('validUntil','截止日期'),('price','已提供的金额'),('currency','币种'),('paymentStatus','付款状态'),('cancellation','用户提供的退改规则'),('note','备注')]
    def entries(records):
        return ['<article class="order-entry" data-order-id="'+esc(t['id'])+'"><div class="order-entry-head"><h4>'+esc(t.get('title') or t.get('name') or '订单待补充')+'</h4>'+badge(t)+'</div><p>'+esc(t['status'])+'</p>'+more(t,extra_fields,private)+'</article>' for t in records]
    tickets=group('ticket','门票与预约',entries(data['tickets']),'门票 / 活动预约待核实或待订；使用日期、时段、人数和入口可继续补充。')
    ground=group('ground','租车与接送',entries(data['groundOrders']),'') if data['groundOrders'] else ''
    other=group('other','其他旅行订单',entries(data['otherOrders']),'') if data['otherOrders'] else ''
    return '<section class="card booking" id="booking" aria-labelledby="booking-title"><div class="booking-head"><h2 id="booking-title">订单与集合</h2></div><p class="order-boundary">区分计划、待付款、已确认和已取消；班次、金额与退改规则按你提供的信息记录。</p><div class="booking-grid">'+traffic+stays+tickets+ground+other+'</div></section>'
