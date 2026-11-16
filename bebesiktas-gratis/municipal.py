import re, unicodedata, subprocess, tempfile
from pathlib import Path
from html.parser import HTMLParser
from urllib.request import Request, urlopen, build_opener, HTTPRedirectHandler
from urllib.parse import urljoin, urlparse
from datetime import datetime
from zoneinfo import ZoneInfo

SOURCE = 'https://deportes.majadahonda.org/futbol-sala-populares'
SEASON = '2026-2027'
GROUP = 'B'

def normalize(s):
    return re.sub(r'[^A-Z0-9]', '', unicodedata.normalize('NFKD', s.upper()).encode('ascii','ignore').decode())

class Links(HTMLParser):
    def __init__(self): super().__init__(); self.links=[]; self.active=None
    def handle_starttag(self, tag, attrs):
        if tag=='a': self.active=[urljoin(SOURCE,dict(attrs).get('href','')), '']
    def handle_data(self, data):
        if self.active: self.active[1]+=data
    def handle_endtag(self, tag):
        if tag=='a' and self.active: self.links.append(self.active); self.active=None

class MunicipalRedirects(HTTPRedirectHandler):
    def redirect_request(self, req, fp, code, msg, headers, newurl):
        p=urlparse(newurl)
        if p.scheme!='https' or p.hostname!='deportes.majadahonda.org': raise ValueError('Destino municipal no permitido')
        return super().redirect_request(req,fp,code,msg,headers,newurl)

def fetch(url, limit=12_000_000):
    p=urlparse(url)
    if p.scheme!='https' or p.hostname!='deportes.majadahonda.org': raise ValueError('Fuente no permitida')
    opener=build_opener(MunicipalRedirects())
    with opener.open(Request(url,headers={'User-Agent':'BebesiktasFS/2.0'}),timeout=25) as r:
        data=r.read(limit+1)
        if len(data)>limit: raise ValueError('Documento demasiado grande')
        return data

def pdf_text(data):
    if not data.startswith(b'%PDF'): raise ValueError('No es un PDF')
    with tempfile.TemporaryDirectory() as tmp:
        path=Path(tmp)/'municipal.pdf'; path.write_bytes(data)
        r=subprocess.run(['pdftotext','-layout',str(path),'-'],capture_output=True,timeout=30)
        if r.returncode: raise ValueError('No se pudo leer el PDF')
        return r.stdout.decode('utf-8','replace')

def parse_standings(text, teams):
    n=normalize(text)
    if not re.search(r'2026\s*[/–-]\s*2027',text) or 'CLASIFICACION' not in n: return None
    headers=[line for line in text.splitlines() if re.search(r'(?:\bG\.\s*B\b|\bGRUPO\s+B\b)',line,re.I)]
    if not headers or any(re.search(r'(?:\bG\.\s*A\b|\bGRUPO\s+A\b)',line,re.I) for line in headers): return None
    by_name={normalize(t['name']):t for t in teams}
    parsed={}
    for line in text.splitlines():
        m=re.match(r'^\s*(\d{1,2})\s*[º°.]?\s+(.+?)\s+(-?\d+)\s+(\d+)\s+(\d+)\s+(\d+)\s+(\d+)\s+(\d+)\s+(-?\d+)\s+(-?\d+)',line)
        if not m: continue
        rank=int(m.group(1)); name=normalize(m.group(2))
        if name not in by_name: continue
        pts,pj,w,d,l,inc,gf,ga=map(int,m.groups()[2:])
        if min(pj,w,d,l,inc,gf,ga)<0 or pj!=w+d+l+inc or pts<0: return None
        if name in parsed: return None
        parsed[name]={'rank':rank,'points':pts,'played':pj,'wins':w,'draws':d,'losses':l,'inc':inc,'gf':gf,'ga':ga}
    if len(parsed)!=len(teams) or sorted(x['rank'] for x in parsed.values())!=list(range(1,len(teams)+1)): return None
    return parsed

def parse_fixtures(text, teams):
    if not re.search(r'2026\s*[/–-]\s*2027',text) or not any(re.search(r'\bG\.\s*B\b',line,re.I) for line in text.splitlines()): return None
    names={normalize(t['name']):t['name'] for t in teams}
    round_no=0; found=[]
    for line in text.splitlines():
        rm=re.search(r'JORNADA\s+(\d+)',line,re.I)
        if rm: round_no=int(rm.group(1))
        m=re.match(r'^\s*\d+\s+(.+?)\s+-\s+(.+?)\s+(\d{2}/\d{2}/\d{4})(?:\s+(\d{2}:\d{2})\s+(.+?))?\s*$',line)
        if not m: continue
        home_key,away_key=normalize(m.group(1)),normalize(m.group(2))
        if home_key not in names or away_key not in names: continue
        if 'BEBESIKTAS' not in (home_key,away_key): continue
        dt=datetime.strptime(m.group(3),'%d/%m/%Y').date().isoformat()
        found.append({'round':round_no,'home':names[home_key],'away':names[away_key],'date':dt,'time':m.group(4),'venue':(m.group(5) or '').strip()})
    if len(found)!=22 or {x['round'] for x in found}!=set(range(1,23)): return None
    return found

def parse_results(text, teams):
    names={normalize(t['name']):t['name'] for t in teams}; results={}
    for line in text.splitlines():
        m=re.match(r'^\s*\d+\s+(.+?)\s+-\s+(.+?)\s+(\d+)\s*[-–]\s*(\d+)\s*$',line)
        if not m: continue
        h,a=normalize(m.group(1)),normalize(m.group(2))
        if h in names and a in names:
            results[(names[h],names[a])]={'homeGoals':int(m.group(3)),'awayGoals':int(m.group(4))}
    return results

def parse_scorers(text, expected_total=None, expected_played=None):
    if not re.search(r'2026\s*[/–-]\s*2027',text) or not any(re.search(r'\bG\.\s*B\b',line,re.I) for line in text.splitlines()): return None
    found={}
    for line in text.splitlines():
        m=re.match(r'^\s*\d+\s*[º°.]?\s+\d+\s+(.+?)\s+BEBESIKTAS\s+(\d+)\s+(\d+)\s+[\d,.]+\s*$',line,re.I)
        if not m: continue
        raw=m.group(1).strip(); goals=int(m.group(2)); played=int(m.group(3))
        if ',' in raw:
            surname, first=raw.split(',',1); name=(first.strip()+' '+surname.strip()).title()
        else: name=raw.title()
        if name in found or goals<0 or played<0: return None
        found[name]=goals
    if not found or len(found)>15: return None
    if expected_total is not None and sum(found.values())!=expected_total: return None
    if expected_played is not None and any(pj>expected_played for pj in [int(re.search(r'\s+(\d+)\s+[\d,.]+\s*$', line).group(1)) for line in text.splitlines() if re.search(r'^\s*\d+\s*[º°.]?\s+\d+\s+.+?\s+BEBESIKTAS\s+\d+\s+\d+\s+[\d,.]+\s*$', line, re.I)]): return None
    return found
