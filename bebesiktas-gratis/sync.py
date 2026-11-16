import os,json
from datetime import datetime, time
from zoneinfo import ZoneInfo
from urllib.request import Request,urlopen
from urllib.parse import urlparse
from municipal import Links,fetch,pdf_text,parse_standings,parse_fixtures,parse_results,parse_scorers,SOURCE,normalize
from pathlib import Path

def pick_document(links, words):
    for url,title in links:
        t=' '.join(title.lower().split())
        if all(w in t for w in words) and 'grupo b' in t: return url,title.strip()[:200]
    return None

def collect():
    parser=Links(); parser.feed(fetch(SOURCE,2_000_000).decode('utf-8','replace'))
    links=[]; seen=set()
    for url,title in parser.links:
        if '.pdf' in url.lower() and urlparse(url).hostname=='deportes.majadahonda.org' and url not in seen:
            links.append((url,title)); seen.add(url)
    calendar=pick_document(links,['calendario','2ª división'])
    standings=pick_document(links,['fútbol sala','2ª division'])
    scorers=pick_document(links,['máximos goleadores','2ª división'])
    # Disambiguate title matches by their exact label text.
    calendar=next(((u,t) for u,t in links if 'calendario' in t.lower() and '2ª división' in t.lower() and 'grupo b' in t.lower()),None)
    standings=next(((u,t) for u,t in links if 'fútbol sala' in t.lower() and '2ª division' in t.lower() and 'grupo b' in t.lower()),None)
    scorers=next(((u,t) for u,t in links if 'máximos goleadores' in t.lower() and '2ª división' in t.lower() and 'grupo b' in t.lower()),None)
    if not all((calendar,standings,scorers)): return {'status':'waiting','documents':[{'url':u,'title':t} for u,t in links[:60]],'message':'La web municipal no muestra todavía los tres documentos necesarios del grupo B. Se conservan los últimos datos válidos.'}
    cal_text=pdf_text(fetch(calendar[0])); std_text=pdf_text(fetch(standings[0])); scor_text=pdf_text(fetch(scorers[0]))
    teams=json.loads(Path('public/league.json').read_text(encoding='utf-8'))['teams']
    parsed=parse_standings(std_text,teams); fixtures=parse_fixtures(cal_text,teams); own=parsed.get(normalize('BEBESIKTAS'),{}) if parsed else {}
    goals=parse_scorers(scor_text,expected_total=own.get('gf'),expected_played=own.get('played'))
    if not parsed or not fixtures or not goals:
        return {'status':'waiting','documents':[{'url':u,'title':t} for u,t in (calendar,standings,scorers)],'message':'Los documentos municipales no superaron las comprobaciones de temporada, grupo, equipos o goleadores. Se conservan los últimos datos válidos.'}
    results=parse_results(std_text,teams)
    now=datetime.now(ZoneInfo('Europe/Madrid'))
    matches=[]
    for f in fixtures:
        home,away=f['home'],f['away']; opponent=away if home=='BEBESIKTAS' else home
        dt=datetime.strptime(f['date'],'%Y-%m-%d').date()
        if opponent=='TABERNA EL FAROL': status='excluded'
        elif (home,away) in results: status='played'
        elif dt<now.date(): status='played_unknown'
        else: status='upcoming'
        date=datetime.combine(dt,time.fromisoformat(f['time']),ZoneInfo('Europe/Madrid')).isoformat() if f['time'] else f['date']
        row={'round':f['round'],'home':home,'away':away,'opponent':opponent,'date':date,'venue':f['venue'],'status':status}
        if (home,away) in results:
            res=results[(home,away)]
            row['for']=res['awayGoals'] if away=='BEBESIKTAS' else res['homeGoals']
            row['against']=res['homeGoals'] if away=='BEBESIKTAS' else res['awayGoals']
        matches.append(row)
    standings_rows=[]
    for t in teams:
        x=parsed[normalize(t['name'])]
        standings_rows.append({'name':t['name'],**x})
    docs=[{'url':u,'title':t} for u,t in (calendar,standings,scorers)]
    return {'status':'updated','season':'2026-2027','group':'B','standings':standings_rows,'matches':matches,'goals':goals,'documents':docs,'message':'Calendario, clasificación y goleadores oficiales del grupo B actualizados.'}

def send(payload):
    base=os.environ['APP_URL'].rstrip('/'); token=os.environ['SYNC_TOKEN']
    if urlparse(base).scheme!='https': raise ValueError('APP_URL debe usar HTTPS')
    body=json.dumps(payload,ensure_ascii=False).encode()
    with urlopen(Request(base+'/api/import',data=body,headers={'Content-Type':'application/json','Authorization':'Bearer '+token}),timeout=30) as r:return json.load(r)

if __name__=='__main__':
    try: payload=collect()
    except Exception as e: payload={'status':'error','message':'No se pudo leer la fuente municipal. Se conservan los últimos datos válidos.'}
    send(payload); print(payload.get('message','Revisión completada'))
