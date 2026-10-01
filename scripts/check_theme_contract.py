"""Static/numeric regression checks; browser rendering is a separate check."""
import re
from pathlib import Path
from theme_tokens import values,contrast

ROOT=Path(__file__).resolve().parent.parent
CASES={
    'japan':dict(bg='#f7f4ed',surface='#fffdf8',ink='#213f60',muted='#6c7780',line='#d8dce0',accent='#213f60',**{'accent-soft':'#e9edf1'}),
    'purple':dict(bg='#faf4fc',surface='#ffffff',ink='#362442',muted='#766280',line='#dfd1e5',accent='#782460',**{'accent-soft':'#f2e2ee'}),
    'bright':dict(bg='#f9faf0',surface='#ffffff',ink='#172838',muted='#677079',line='#d9ddd0',accent='#ffe26b',**{'accent-soft':'#fff6cf'}),
}
def check():
    page=(ROOT/'assets/original-template.html').read_text(encoding='utf-8')
    css=''.join(re.findall(r'<style>(.*?)</style>',page,re.S))
    assert not re.search(r'#[0-9a-fA-F]{3,8}\b|rgba?\(',css), 'Historic hardcoded paint remains in base UI CSS'
    control=(ROOT/'assets/control-theme.css').read_text(encoding='utf-8')
    for state in [':hover',':active','.is-pressing',':focus-visible',':disabled','[aria-selected=true]','[aria-current=location]','.hotel-map-link::before']:
        assert state in control,state+' missing from paint contract'
    builder=(ROOT/'scripts/build_original.py').read_text(encoding='utf-8')
    assert "'control-theme.css'" in builder and "get('stylesheet')" in builder
    assert not re.search(r'background:#[0-9a-fA-F]|stroke:#[0-9a-fA-F]',builder), 'Generator injects historical UI paint'
    for name,palette in CASES.items():
        colors=values({'visualTheme':{'palette':palette}})
        pairs=[('accent','on-accent'),('accent-hover','on-accent-hover'),('accent-pressed','on-accent-pressed'),('accent-soft','on-soft'),('soft-hover','on-soft-hover'),('soft-pressed','on-soft-pressed'),('disabled-surface','disabled-ink'),('nav-surface','nav-ink')]
        scores={a:round(contrast(colors[a],colors[b]),2) for a,b in pairs}
        assert all(score>=4.5 for score in scores.values()),(name,scores)
        print(name,scores)
    print('Static and numeric theme contract passed; browser/physical phone verification is separate.')
if __name__=='__main__':check()
