"""Daily editorial summaries with one consistent, local SVG icon vocabulary."""
import html

PATHS={
 'plane':'<path d="m3 14 7-3 1-8h2l1 8 7 3v2l-7-1-1 6h-2l-1-6-7 1v-2Z"/>',
 'train':'<rect x="6" y="3" width="12" height="15" rx="3"/><path d="M6 10h12M8 21l2-3m4 0 2 3M9 14h.01M15 14h.01"/>',
 'car':'<path d="m3 12 3-7h12l3 7v7H3v-7Zm0 0h18M6 19v2m12-2v2M6 15h2m8 0h2"/>',
 'bike':'<circle cx="6" cy="16" r="4"/><circle cx="18" cy="16" r="4"/><path d="m6 16 5-9 7 9h-8L7 7h4m4-3h3l-2 5"/>',
 'coast':'<path d="M3 18q3-4 6 0t6 0t6 0M3 22q3-4 6 0t6 0t6 0M4 11q6-11 12 0H4Zm6 0v6"/><circle cx="19" cy="5" r="2"/>',
 'nature':'<path d="m3 20 6-12 4 7 3-11 5 16H3Z"/><circle cx="5" cy="4" r="2"/>',
 'landmark':'<path d="m3 9 9-6 9 6H3ZM5 10v10m5-10v10m4-10v10m5-10v10M3 21h18"/>',
 'city':'<path d="M3 21V9h6V3h6v10h6v8H3ZM6 13h.01M6 17h.01M12 7h.01M12 11h.01M12 15h.01M18 17h.01"/>',
 'food':'<path d="M4 3v6q3 4 6 0V3M7 3v18M18 3q-5 5 0 10v8M18 3v10"/>',
 'rest':'<path d="M3 18V9h18v9M3 15h18M3 21v-3m18 3v-3M6 9V6h12v3"/>',
 'route':'<circle cx="5" cy="5" r="2"/><circle cx="19" cy="19" r="2"/><path d="M7 5h7a4 4 0 0 1 0 8H9a4 4 0 0 0 0 8h8"/>'}

def icon(name):
    return '<svg class="ui-icon itinerary-icon" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.7" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true">'+PATHS.get(name,PATHS['route'])+'</svg>'

def details(day):
    title=day.get('previewTitle') or day.get('headline') or day['city']
    summary=day.get('previewSummary') or day['summary']
    name=day.get('previewIcon')
    if name not in PATHS:
        text=' '.join([str(title),str(summary)]+[e['title'] for e in day['events']])
        rules=[('plane',('飞机','航班','机场')),('train',('火车','高铁','车站')),('bike',('骑行','自行车')),('car',('自驾','取车')),('coast',('沙滩','海岸','海边')),('nature',('草原','山林','徒步')),('landmark',('博物馆','寺庙','古城')),('food',('夜市','美食','小吃')),('rest',('休息','入住'))]
        name=next((name for name,words in rules if any(word in text for word in words)),'route')
    return dict(title=str(title),summary=str(summary),icon=name)

def cards(days):
    esc=lambda x:html.escape(str(x),quote=True)
    chevron='<svg class="ui-icon" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true"><path d="m6 9 6 6 6-6"/></svg>'
    result=[]
    for i,d in enumerate(days):
        p=details(d)
        result.append('<button class="route-day" type="button" data-route-day="'+str(i)+'" style="--route-color:var(--day'+str(i%4+1)+')" aria-label="第 '+str(i+1)+' 天 · '+esc(d['city'])+' · 展开预览" aria-pressed="'+str(i==0).lower()+'"><div class="route-day-top"><span class="route-date">第 '+str(i+1)+' 天</span></div><strong class="route-city">'+esc(d['city'])+'</strong><div class="route-summary">'+icon(p['icon'])+'<div>'+('<b class="route-headline">'+esc(p['title'])+'</b>' if p['title']!=d['city'] else '')+'<span class="route-brief">'+esc(p['summary'])+'</span><small class="route-state">'+esc(d['status'])+'</small></div></div><span class="route-day-footer" aria-hidden="true">'+chevron+'</span></button>')
    return ''.join(result)
