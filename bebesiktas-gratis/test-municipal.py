import unittest,json
from pathlib import Path
from municipal import parse_standings,parse_fixtures,parse_results,parse_scorers
class Tests(unittest.TestCase):
 def setUp(self): self.teams=json.loads(Path('public/league.json').read_text())['teams']
 def test_group_b_standings_and_rejections(self):
  rows=['Temporada 2026/2027','CLASIFICACIONES','Grupo: 05- FUTBOL SALA 2ª División - G. B - Liga']+[f'{i}º {t["name"]} 3 1 1 0 0 0 4 1 3 4,00 0 =' for i,t in enumerate(self.teams,1)]
  text='\n'.join(rows); self.assertEqual(len(parse_standings(text,self.teams)),12)
  self.assertIsNone(parse_standings(text.replace('G. B','G. A'),self.teams))
  self.assertIsNone(parse_standings(text.replace('2026/2027','2025/2026'),self.teams))
  self.assertIsNone(parse_standings('\n'.join(rows[:-1]),self.teams))
 def test_official_scorers_and_score(self):
  text='Temporada 2026-2027\nGrupo: 2ª División - G. B\n8º 14906 SILVEIRA IRIBARREN, LUIS PEDRO BEBESIKTAS 4 4 1,00\n35º 2572 ULECIA HORMAECHEA, RAFAEL BEBESIKTAS 2 4 0,50\n37º 31688 SANCHEZ SAZ, JOSE BEBESIKTAS 2 4 0,50\n38º 32240 PEREZ ROSALES, ADRIAN BEBESIKTAS 2 4 0,50\n57º 14916 ATENCIA MARTIN, PABLO BEBESIKTAS 1 4 0,25\n60º 2212 MATEO VELA, PABLO BEBESIKTAS 1 4 0,25\n66º 2282 LOPEZ ORTEGA, SERGIO BEBESIKTAS 1 4 0,25'
  parsed=parse_scorers(text,expected_total=13,expected_played=4); self.assertEqual(sum(parsed.values()),13); self.assertEqual(len(parsed),7)
  results=parse_results('2 SPORTING DE MAJADAHONDA - BEBESIKTAS 5-8',self.teams); self.assertEqual(results[('SPORTING DE MAJADAHONDA','BEBESIKTAS')]['awayGoals'],8)
 def test_22_fixtures(self):
  rows=['Temporada 2026-2027','Grupo: 2ª División - G. B - Liga']
  fixtures=[(1,'MACAME','BEBESIKTAS','18/10/2026 14:00 P.FELIPE Pista Central'),(2,'LA PLAZA CCC','BEBESIKTAS','25/10/2026 18:00 LA GRANADILLA')]
  # Full round count contract is tested with a generated minimal schedule.
  for i in range(1,23):
   h,a=('MACAME','BEBESIKTAS') if i%2 else ('BEBESIKTAS','MACAME')
   rows += [f'JORNADA {i}',f'1 {h} - {a} {i:02d}/01/2027 10:00 LA GRANADILLA']
  parsed=parse_fixtures('\n'.join(rows),self.teams); self.assertEqual(len(parsed),22)
if __name__=='__main__': unittest.main()
