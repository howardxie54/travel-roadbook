"""Run a deterministic fixture, not an independent agent evaluation."""
import copy
import json
import sys
from pathlib import Path
from build import build
from build_original import build as build_preserved


def write(path, data):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding='utf-8')


root = Path(__file__).resolve().parent.parent
out = Path(sys.argv[1])
fixture = json.loads((root / 'examples' / 'thailand-test.json').read_text(encoding='utf-8'))
trip = dict(title='曼谷与芭提雅', subtitle='从城市抵达海岸。先留出七天，再慢慢补齐每一段安排。', origin='上海', duration=7, timezone='Asia/Bangkok', dates=None, flight=None, contentVersion='c0', styleVersion='s0', theme=dict(direction='a', large=False), days=[], bookings=[], conflicts=[], pending=['出发日期、往返机场与航班尚未提供。','城市之间的交通方式、车站与时刻待确认。','第 4—7 天分配为助手暂拟，返程城市待确认。','同行人数、兴趣偏好和活动安排待补充。'], sources=[], testMode=True, routeLabel='SHANGHAI → BANGKOK → PATTAYA', visualLine='城市与海岸之间', disclaimer='测试路书 · 酒店名称与地址均为虚构。日期、航班及活动尚未确认，不作为实际出行依据。')
trip['transports']=[dict(mode='飞机',**{'from':'上海','to':'曼谷'},status='用户计划 · 未提供班次',note='到达机场、起降时刻与行李信息待补充。')]
trip['routeNodes']=[dict(label='上海',x=110,y=105,mode='plane'),dict(label='曼谷',x=260,y=285,mode='unknown'),dict(label='芭提雅',x=450,y=410,mode='unknown')]
for n in range(1, 8):
    city = '曼谷' if n < 3 else '芭提雅' if n < 7 else '返程城市待定'
    trip['days'].append(dict(id='day-'+str(n), number=n, city=city, status='暂定', summary='城市分配为暂拟，可随酒店与交通调整。', events=[dict(id='event-'+str(n), title='抵达与休息' if n == 1 else '城市活动待补充' if n < 7 else '返程衔接待补充', detail='用户尚未提供具体时刻、地点或活动；此处不作已确认安排。', status='待补充')]))


def snapshot(name, value, message):
    write(out / 'history' / (name + '.json'), dict(message=message, trip=value))
    write(out / name / 'trip.json', value)
    build(value, out / name / 'index.html')
    build_preserved(value, out / name / 'original-style.html', out / name)


snapshot('00-initial', trip, fixture['initial'])
alt = copy.deepcopy(trip)
alt['theme']['direction'] = 'b'
build(alt, out / '00-initial' / 'direction-b.html')
trip['bookings'] = copy.deepcopy(fixture['syntheticBookings'])
trip['contentVersion'] = 'c1'
trip['days'][2].update(city='曼谷 → 芭提雅', summary='上午仍在曼谷，之后前往芭提雅；交通方式和时刻待确认。')
snapshot('01-bookings', trip, fixture['updates'][0])
before = copy.deepcopy(trip)
trip['contentVersion'] = 'c2'
trip['days'][1].update(city='曼谷 → 芭提雅', summary='用户改为第二天去芭提雅；当天往返还是提前过夜尚未说明。')
trip['days'][2].update(city='待确认', summary='若第二天已前往芭提雅，第三天上午是否仍在曼谷需要确认。')
trip['conflicts'] = ['第二天去芭提雅，但曼谷第 2 晚仍有测试预订。是当天往返还是提前过夜？若提前过夜，请确认是否改订；本路书未取消任何预订。','原计划第三天上午仍在曼谷，与提前前往芭提雅的安排需要一起确认。']
snapshot('02-earlier-transfer', trip, fixture['updates'][1])
style_before = copy.deepcopy(trip['theme'])
trip['theme']['large'] = True
trip['theme']['atmosphere'] = True
trip['styleVersion'] = 's1'
snapshot('03-larger-type', trip, fixture['updates'][2])
# Ambiguous rollback does not change the current project.
snapshot('04-rollback-pending', trip, fixture['updates'][3])
write(out / 'rollback-request.json', dict(status='awaiting-clarification', question='要恢复修改前的样式 s0，保留最新行程 c2；还是恢复某个完整行程版本？', candidates=['02-earlier-transfer: c2/s0','01-bookings: c1/s0','00-initial: c0/s0']))
demo = copy.deepcopy(trip)
demo['theme'] = style_before
demo['styleVersion'] = 's0'
snapshot('05-style-restore-example', demo, '演示分支：只有在用户明确选择恢复样式后才执行；不是当前状态。')
write(out / 'trip.json', trip)
build(trip, out / 'index.html')
build_preserved(trip, out / 'original-style.html', out)
assert trip['bookings'] == before['bookings']
assert len(trip['conflicts']) == 2
assert trip['days'] == demo['days'] and trip['bookings'] == demo['bookings']
assert trip['contentVersion'] == demo['contentVersion'] == 'c2'
assert trip['theme'] != demo['theme']
assert trip['dates'] is None and trip['flight'] is None
write(out / 'validation.json', dict(generatorInvariants='passed', checks=['unknown dates and flight preserved','bookings retained across transfer conflict','visual restoration preserves content','ambiguous restoration leaves current state intact'], independentAgentEvaluation='not performed'))
print('Generated fixture snapshots and two initial directions. Invariants passed.')
