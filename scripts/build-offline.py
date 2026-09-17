"""Export the current trip to a script-free, self-contained HTML and phone PDF."""
import base64
import html
import json
from pathlib import Path
from xml.sax.saxutils import escape

from PIL import Image as PILImage
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.lib import colors
from reportlab.lib.styles import ParagraphStyle
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, PageBreak, KeepTogether, Image, Flowable

ROOT = Path(__file__).resolve().parent.parent
OUT = ROOT / 'output/offline'
PDFOUT = ROOT / 'output/pdf'
MAPS = Path('/private/tmp/travel-offline-maps')
OUT.mkdir(parents=True, exist_ok=True)
PDFOUT.mkdir(parents=True, exist_ok=True)
D = json.loads((ROOT / 'trip-data.json').read_text())
PLACES = {p['id']: p for p in D['places']}
HOTELS = {p['id']: p for p in D['accommodations']}
TICKETS = {p['id']: p for p in D['ticketPlanning']['items']}

def clean(s):
    return str(s).replace('—', '-').replace('–', '-').replace('‑', '-')

def e(s):
    return html.escape(clean(s), quote=True)

def short_date(s):
    return f"{int(s[5:7])}/{int(s[8:10])}"

def ticket_text(t):
    if t.get('guidance'):
        return ' '.join(t['guidance']).replace('已设置9/23 09:00提醒。', '')
    return t['requirement']

def hotel_for(s):
    if s.get('type') != 'check-in':
        return None
    ids = [s.get('placeId')] + s.get('placeIds', [])
    return next((HOTELS[x] for x in ids if x in HOTELS), None)

def schedule_content(s, day):
    # Rental details in the quick reference are deliberately only pickup/return.
    if s['id'] == 'd4-5':
        return '大理凤仪机场取车，具体门店或交接点待补充。'
    return s['text']

def day_blocks(day):
    result = []
    shown = set()
    for s in day['schedule']:
        result.append(('time', s['time']))
        result.append(('body', schedule_content(s, day)))
        h = hotel_for(s)
        if h:
            result.append(('hotel', h['name'] + ('（暂定）' if h.get('status') == 'tentative' else '')))
            result.append(('address', h.get('address', '地址待确认')))
        policy = D.get('mapLinks', {}).get('navigationPolicy', {})
        if s.get('navigation') is not False and s.get('type') not in policy.get('noNavigationTypes', []):
            ids = list(dict.fromkeys(([s['placeId']] if s.get('placeId') else []) + s.get('placeIds', [])))
            for pid in ids:
                place = PLACES.get(pid)
                if place and place.get('navigation', {}).get('url'):
                    result.append(('navigation', place))
        for tid in s.get('ticketIds', []):
            if tid in shown:
                continue
            shown.add(tid)
            t = TICKETS[tid]
            result.append(('ticket', t['name'] + '｜' + ticket_text(t)))
    for n in day.get('notes', []):
        result.append(('note', n))
    return result

css = '''
:root{color-scheme:light;--ink:#203e35;--accent:#55774e;--paper:#f4f5ee;--line:#dbe2d4}
*{box-sizing:border-box}html{scroll-behavior:smooth}body{margin:0;background:var(--paper);color:var(--ink);font:16px/1.7 -apple-system,BlinkMacSystemFont,'PingFang SC','Microsoft YaHei',sans-serif}
main{max-width:740px;margin:auto;padding:22px 16px 60px}h1{font-size:clamp(16px,4.5vw,30px);white-space:nowrap;line-height:1.4;letter-spacing:-.6px;margin:10px 0}h2{font-size:24px;line-height:1.4;margin:5px 0 16px}h3{font-size:17px;margin:0}p{margin:7px 0}.eyebrow{font-size:12px;letter-spacing:2px;color:#687e60}.muted{color:#657263;font-size:13px}.notice{padding:13px 15px;border-left:3px solid #81936b;background:#e9edde;font-size:13px;margin:18px 0}
nav{display:flex;flex-wrap:wrap;gap:8px;margin:18px 0 26px}a{color:#355f45;text-decoration:underline;text-underline-offset:3px}nav a{display:block;padding:5px 12px;border:1px solid var(--line);border-radius:20px;background:#fff;text-decoration:none;font-size:14px}
section{scroll-margin-top:18px;margin:28px 0}.card{background:#fff;border:1px solid var(--line);border-radius:16px;padding:18px;margin:13px 0}.flight{padding:17px 18px}.flight-top{display:flex;justify-content:space-between;gap:12px;font-size:13px;color:#657263}.flight-route{display:grid;grid-template-columns:1fr 26px 1fr;align-items:center;margin:10px 0}.clock{font:700 34px/1.2 ui-monospace,monospace;letter-spacing:-1px}.arrival{text-align:right}.next{font-size:12px;color:#9d592d}.airport{font-size:13px;margin-top:5px}.car{display:grid;grid-template-columns:1fr 1fr;gap:16px}.car strong{font-size:25px}.car p{font-size:13px}.event{padding:14px 0;border-bottom:1px solid #e9eddf}.event:last-child{border:0}.time{font-weight:700;color:#47724c;font-size:14px}.hotel{font-weight:600;margin-top:9px}.address{font-size:13px;color:#657263}.ticket,.note{background:#f0f2e5;padding:11px 13px;border-radius:8px;margin-top:11px;font-size:14px}.map{width:100%;height:auto;display:block;border-radius:9px}.map-places{font-size:14px}.back{font-size:13px;display:block;margin-top:20px}.footer{border-top:1px solid var(--line);padding-top:18px;color:#657263;font-size:12px}
@media print{body{background:#fff}.card{break-inside:avoid}nav{display:none}}
'''

parts = [f'<!doctype html><html lang="zh-CN"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><meta name="format-detection" content="telephone=no"><title>双人秋日旅行 · 手机离线版</title><style>{css}</style></head><body><main id="top">',
 '<div class="eyebrow">AUTUMN JOURNEY / OFFLINE EDITION</div><h1>贵阳 · 大理 · 泸沽湖 · 丽江</h1>',
 '<p>2026.09.25 - 10.07 · 2 人 · 重庆回家</p>',
 '<div class="notice">此文件已内置全部行程和四张路线图，无需联网加载。地图为行程示意，可放大查看。高德定位链接需联网；实时导航请使用已下载离线地图的地图 App。信息快照：2026/9/17，暂定事项仍需确认。</div>',
 '<nav aria-label="快速跳转"><a href="#flights">机票</a><a href="#drive">取还车</a>']
parts.extend(f'<a href="#day-{d["day"]}">{short_date(d["date"])}</a>' for d in D['days'])
parts.extend(f'<a href="#map-{r["id"]}">{e(r["label"])}地图</a>' for r in D['routeMap']['regions'])
parts.append('</nav><section id="flights"><div class="eyebrow">BOARDING</div><h2>机票速查</h2>')
for f in D['flights']:
    dep, arr = f['departure'], f['arrival']
    nxt = '<span class="next">次日 '+short_date(arr['date'])+'</span>' if dep['date'] != arr['date'] else ''
    parts.append(f'<article class="card flight"><div class="flight-top"><span>{short_date(dep["date"])} · {e(f["flightNumber"])}</span><span>{e(f["airline"]["name"])}</span></div><div class="flight-route"><div><div class="clock">{dep["time"]}</div><div class="airport">{e(dep["airportName"])} {dep["terminal"]}</div></div><div>→</div><div class="arrival"><div class="clock">{arr["time"]}</div><div class="airport">{e(arr["airportName"])} {arr["terminal"]} {nxt}</div></div></div></article>')
parts.append('<p class="muted">均为北京时间；航班时刻与航站楼以承运人最新通知为准。</p></section><section id="drive"><div class="eyebrow">ON THE ROAD</div><h2>取车与还车</h2><div class="card car">')
rental = D['groundTransport']['rentalCar']
for key, label in [('pickup','PICKUP'),('dropoff','RETURN')]:
    p = rental[key]
    parts.append(f'<div><div class="eyebrow">{label} · {short_date(p["date"])}</div><strong>{p["time"]}</strong><p>{e(p["location"])}</p></div>')
parts.append('</div></section>')
for day in D['days']:
    parts.append(f'<section id="day-{day["day"]}" class="card day"><div class="eyebrow">DAY {day["day"]:02d} / {short_date(day["date"])}</div><h2>{e(day["title"])}</h2>')
    opened = False
    for kind, text in day_blocks(day):
        if kind == 'time':
            if opened: parts.append('</div>')
            parts.append('<div class="event">')
            opened = True
        if kind == 'navigation':
            parts.append(f'<a class="muted" href="{e(text["navigation"]["url"])}" target="_blank" rel="noopener noreferrer">在高德地图打开 ↗</a> ')
        else:
            parts.append(f'<p class="{kind}">{e(text)}</p>')
    if opened: parts.append('</div>')
    parts.append('<a class="back" href="#top">回到日期目录 ↑</a></section>')
for r in D['routeMap']['regions']:
    raw = (MAPS / (r['id'] + '.jpg')).read_bytes()
    names = [PLACES[p].get('nameZh', PLACES[p].get('name',p)) for p in r.get('overviewPlaceIds',[]) if p in PLACES]
    parts.append(f'<section id="map-{r["id"]}" class="card"><div class="eyebrow">OFFLINE ROUTE MAP</div><h2>{e(r["label"])} · 路线示意</h2><img class="map" alt="{e(r["label"])}离线路线图" src="data:image/jpeg;base64,{base64.b64encode(raw).decode()}"><p class="map-places">{e(" / ".join(names))}</p><p class="muted">沿用旅行网页地图，表示相对位置与行程顺序，不用于转向导航或精确距离判断。</p><a class="back" href="#top">回到目录 ↑</a></section>')
parts.append('<footer class="footer">离线快照不会自动更新。此文件不触发预约提醒，也不包含未购买的门票凭证。可直接把完整文件发送给同行人。</footer></main></body></html>')
html_path = OUT / '双人秋日旅行-手机离线版.html'
html_path.write_text(''.join(parts))

# A narrow portrait PDF readable in phone file viewers, with an outline and date links.
pdfmetrics.registerFont(TTFont('TravelCN','/System/Library/Fonts/Supplemental/Arial Unicode.ttf'))
INK=colors.HexColor('#203e35'); GREEN=colors.HexColor('#55774e'); MUTED=colors.HexColor('#63715f')
styles = {
 'title': ParagraphStyle('title',fontName='TravelCN',fontSize=23,leading=33,textColor=INK,spaceAfter=10),
 'heading': ParagraphStyle('heading',fontName='TravelCN',fontSize=20,leading=29,textColor=INK,spaceAfter=12),
 'body': ParagraphStyle('body',fontName='TravelCN',fontSize=14,leading=21,textColor=INK,spaceAfter=8,wordWrap='CJK'),
 'time': ParagraphStyle('time',fontName='TravelCN',fontSize=13,leading=19,textColor=GREEN,spaceBefore=9,spaceAfter=4,keepWithNext=True,wordWrap='CJK'),
 'small': ParagraphStyle('small',fontName='TravelCN',fontSize=11,leading=17,textColor=MUTED,spaceAfter=7,wordWrap='CJK'),
 'hotel': ParagraphStyle('hotel',fontName='TravelCN',fontSize=13,leading=20,textColor=INK,spaceAfter=4,wordWrap='CJK'),
 'note': ParagraphStyle('note',fontName='TravelCN',fontSize=12,leading=18,textColor=INK,backColor=colors.HexColor('#edf1e4'),borderPadding=9,spaceBefore=12,spaceAfter=13,wordWrap='CJK'),
 'clock': ParagraphStyle('clock',fontName='Helvetica-Bold',fontSize=28,leading=35,textColor=INK,spaceAfter=3),
}
def para(text, style='body'):
    return Paragraph(escape(clean(text)), styles[style])

class Mark(Flowable):
    def __init__(self,key,title):
        super().__init__(); self.key=key; self.title=title; self.width=0; self.height=0
    def draw(self):
        self.canv.bookmarkPage(self.key)
        self.canv.addOutlineEntry(self.title,self.key,0)

def page_decor(canvas, doc):
    canvas.setFillColor(colors.HexColor('#f5f6ef')); canvas.rect(0,0,390,780,fill=1,stroke=0)
    canvas.setStrokeColor(colors.HexColor('#dbe2d4')); canvas.line(24,36,366,36)
    canvas.setFont('TravelCN',9); canvas.setFillColor(MUTED)
    canvas.drawString(24,22,'双人秋日旅行 · 离线快照 2026/9/17')
    canvas.drawRightString(366,22,str(doc.page))

story=[Mark('top','机票与取还车速查'),para('双人秋日旅行','title'),para('贵阳 · 大理 · 泸沽湖 · 丽江','hotel'),para('2026/9/25 - 10/7 · 2 人 · 重庆回家','small')]
for f in D['flights']:
    dep,arr=f['departure'],f['arrival']
    label=f"{short_date(dep['date'])}   {f['flightNumber']} · {f['airline']['name']}"
    route=f"{dep['airportName']} {dep['terminal']} → {arr['airportName']} {arr['terminal']}"
    if dep['date'] != arr['date']: route+=f"（次日 {short_date(arr['date'])} 抵达）"
    story.append(KeepTogether([para(label,'time'),para(f"{dep['time']}  >  {arr['time']}",'clock'),para(route,'small')]))
story.extend([Spacer(1,4),para('PICKUP  9/28 19:30 · 大理凤仪机场','hotel'),para('RETURN  9/30 19:30 · 大理古城东门','hotel'),para('所有时间为北京时间。班次及航站楼以最新通知为准；具体取还车交接点待确认。','small')])
links='  /  '.join(f'<link href="#day-{d["day"]}" color="#355f45">{short_date(d["date"])}</link>' for d in D['days'])
story.extend([para('点击日期跳转行程','time'),Paragraph(links,styles['small']),para('文件已内置行程和地图，无需联网阅读。示意图可放大；实时导航与预约需联网。','small')])

normal_styles = styles
for day in D['days']:
    styles = normal_styles
    if day['day'] in [7, 8]:
        styles = {name: ParagraphStyle('compact-'+name, parent=style, fontSize=style.fontSize * .94, leading=style.leading * .90, spaceAfter=style.spaceAfter * .75, spaceBefore=style.spaceBefore * .75) for name, style in normal_styles.items()}
    # Keep home-only days together; preserve all dates and return flight details.
    if day['day'] not in [11,12,13]: story.append(PageBreak())
    elif day['day'] == 13: story.append(Spacer(1,16))
    story.extend([Mark(f'day-{day["day"]}',f'{short_date(day["date"])} {day["title"]}'),para(f'{short_date(day["date"])} / DAY {day["day"]:02d}','small'),para(day['title'],'heading')])
    blocks=day_blocks(day)
    for kind,text in blocks:
        if kind in ['time','body','hotel']: story.append(para(text,kind))
        elif kind == 'address': story.append(para(text,'small'))
        elif kind == 'navigation':
            story.append(Paragraph(f'<link href="{e(text["navigation"]["url"])}" color="#355f45">在高德地图打开</link>',styles['small']))
        else: story.append(para(text,'note'))
    if day['day'] in [10,11,12]: story.append(Spacer(1,12))

styles = normal_styles
for r in D['routeMap']['regions']:
    story.extend([PageBreak(),Mark('map-'+r['id'],r['label']+'路线图'),para('离线路线图','small'),para(r['label'],'heading')])
    p=MAPS/(r['id']+'.jpg')
    w,h=PILImage.open(p).size
    story.append(Image(str(p),width=342,height=342*h/w))
    story.extend([Spacer(1,18),para('地图可双指放大查看。表示相对位置与行程顺序，不用于转向导航或精确距离判断。','small')])
    route_days=[d for d in D['days'] if d['day'] in r.get('days',[])]
    for d in route_days:
        story.append(para(f'{short_date(d["date"])} · {d["title"]}','body'))
    names=[PLACES[p].get('nameZh',PLACES[p].get('name',p)) for p in r.get('overviewPlaceIds',[]) if p in PLACES]
    story.append(para('图中地点：'+' / '.join(names),'small'))

pdf_path = PDFOUT / '双人秋日旅行-手机离线版.pdf'
doc=SimpleDocTemplate(str(pdf_path),pagesize=(390,780),rightMargin=24,leftMargin=24,topMargin=28,bottomMargin=51,title='双人秋日旅行 - 手机离线版',author='旅行计划',pageCompression=1)
doc.build(story,onFirstPage=page_decor,onLaterPages=page_decor)
(OUT/'使用说明.txt').write_text('手机离线版\n\n优先使用 PDF：发送到手机后，保存到“文件”或阅读器，确认已下载，再开飞行模式检查。\nHTML 是单文件离线网页，行程和图片已内置，无需运行脚本。请用支持本地 HTML 的应用打开；若系统预览不能打开，使用 PDF。\n地图为路线示意，可缩放阅读；高德定位链接需要联网。\n离线文件不会自动更新，不触发预约提醒。待确认的交通、门票与民宿预订仍需落实。\n')
print(json.dumps({'html':str(html_path),'pdf':str(pdf_path),'html_bytes':html_path.stat().st_size,'pdf_bytes':pdf_path.stat().st_size},ensure_ascii=False))
