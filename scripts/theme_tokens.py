"""Build theme-derived navigation and readable foreground tokens without extra tools."""
import re

DEFAULT=dict(bg='#faf7ef',surface='#fffdf7',ink='#3e3a32',muted='#777063',line='#ded7c8',accent='#70634f',**{'accent-soft':'#f1ebdf'})
THAILAND=dict(bg='#fff8e9',surface='#fffdf6',ink='#493719',muted='#786646',line='#e7d6ac',accent='#9a5b12',**{'accent-soft':'#ffecb5'})
def rgb(value):
    value=value.lstrip('#');value=''.join(c*2 for c in value) if len(value)==3 else value
    return tuple(int(value[i:i+2],16) for i in (0,2,4))
def hex_color(values):return '#'+''.join('{:02x}'.format(round(v)) for v in values)
def mix(a,b,fraction):return hex_color([x*(1-fraction)+y*fraction for x,y in zip(rgb(a),rgb(b))])
def luminance(color):
    values=[v/255 for v in rgb(color)];values=[v/12.92 if v<=.04045 else ((v+.055)/1.055)**2.4 for v in values]
    return sum(v*w for v,w in zip(values,(.2126,.7152,.0722)))
def contrast(a,b):
    x,y=sorted([luminance(a),luminance(b)]);return (y+.05)/(x+.05)
def foreground(background,preferred):
    if contrast(background,preferred)>=4.5:return preferred
    return max(['#171717','#ffffff'],key=lambda c:contrast(background,c))
def palette(data):
    colors=dict(THAILAND if data.get('destinationTheme')=='thailand-summer' else DEFAULT)
    for key,value in (data.get('visualTheme',{}).get('palette') or {}).items():
        if key in colors and isinstance(value,str) and re.fullmatch(r'#[0-9a-fA-F]{3}(?:[0-9a-fA-F]{3})?',value):colors[key]=value
    return colors
def values(data):
    p=palette(data);nav=mix(p['accent-soft'],p['accent'],.24);ink=foreground(nav,p['ink']);r,g,b=rgb(nav);sr,sg,sb=rgb(p['surface']);ar,ag,ab=rgb(p['accent'])
    extra={'on-accent':foreground(p['accent'],p['surface']),'nav-surface':nav,'nav-ink':ink,'nav-hover':mix(nav,p['accent'],.10),'nav-glass':'rgba({},{},{},.94)'.format(r,g,b),'mobile-glass':'rgba({},{},{},.6)'.format(sr,sg,sb),'nav-shadow':'rgba({},{},{},.18)'.format(ar,ag,ab)}
    for state,fraction in [('hover',.13),('pressed',.25)]:
        color=mix(p['accent'],'#000000' if luminance(p['accent'])<.3 else p['ink'],fraction)
        extra['accent-'+state]=color
        extra['on-accent-'+state]=foreground(color,p['surface'])
        soft=mix(p['accent-soft'],p['accent'],fraction)
        extra['soft-'+state]=soft
        extra['on-soft-'+state]=foreground(soft,p['ink'])
    disabled=mix(p['surface'],p['line'],.5)
    extra.update({'on-soft':foreground(p['accent-soft'],p['ink']),
                  'disabled-surface':disabled,'disabled-ink':foreground(disabled,p['muted']),
                  'focus-ring':foreground(p['surface'],p['accent']),
                  'surface-glass':'rgba({},{},{},.94)'.format(sr,sg,sb),
                  'control-shadow':'rgba({},{},{},.18)'.format(ar,ag,ab),
                  'warm':p['accent-soft'],'clay':p['accent'],'clay-text':p['accent'],
                  'route-node':p['accent'],'route-thread':p['line'],
                  'sand-card':p['accent-soft'],'sand-stroke':p['line'],
                  'day1':p['accent'],'day2':p['ink'],
                  'day3':mix(p['accent'],p['muted'],.35),'day4':p['muted']})
    return dict(p,**extra)

def tokens(data):
    return ':root{'+''.join('--'+k+':'+v+';' for k,v in values(data).items())+'}'
