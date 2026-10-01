import json
import sys
from pathlib import Path


def build(data, output):
    template = (Path(__file__).resolve().parent.parent / 'assets' / 'template.html').read_text(encoding='utf-8')
    payload = json.dumps(data, ensure_ascii=False).replace('<', '\\u003c').replace('>', '\\u003e').replace('&', '\\u0026')
    # Generic defaults; destination-specific copy is supplied by project data.
    html = template.replace('__DATA__', payload)
    import html as html_module
    for token, value in {
        'SHANGHAI → BANGKOK → PATTAYA': data.get('routeLabel', data.get('origin', '') + ' → ' + data['title']),
        '七天，慢慢展开': str(data['duration']) + ' 天，慢慢展开',
        '测试路书 · 酒店名称与地址均为虚构。日期、航班及活动尚未确认，不作为实际出行依据。': data.get('disclaimer', '暂定内容请在出发前确认。'),
    }.items():
        # Only replace template copy, never the embedded JSON.
        before, after = html.split('<script type="application/json"', 1)
        html = before.replace(token, html_module.escape(value)) + '<script type="application/json"' + after
    html = html.replace("line.textContent='城市与海岸之间'", "line.textContent=trip.visualLine||'随身旅行计划'")
    html = html.replace("'航班待补充'", "trip.flight||'航班待补充'")
    html = html.replace("render(0);", "render(0);if(trip.theme.atmosphere){document.querySelector('.hero').style.background='linear-gradient(125deg,#d9efeb 0%,#edf5f4 58%,#dae7f1 100%)';document.querySelector('.hero').style.paddingInline='20px';}")
    output = Path(output)
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(html, encoding='utf-8')
    return output


if __name__ == '__main__':
    build(json.loads(Path(sys.argv[1]).read_text(encoding='utf-8-sig')), sys.argv[2])
