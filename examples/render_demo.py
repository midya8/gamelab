"""Exact game data; only spatial display arithmetic uses floats."""
import base64
from fractions import Fraction as F
import html
import json
from pathlib import Path
import sys
import zlib
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from gamelab import demo


def render(r):
    out=['<svg xmlns="http://www.w3.org/2000/svg" width="1120" height="1210" viewBox="0 0 1120 1210">',
         '<rect width="1120" height="1210" fill="#f4f1ed"/><rect x="16" y="16" width="1088" height="1178" rx="18" fill="white"/>',
         '<style>text{font-family:Arial,sans-serif;fill:#292929}.muted{fill:#666}</style>']
    def text(x,y,s,size=17,extra=''):out.append(f'<text x="{x}" y="{y}" font-size="{size}" {extra}>{html.escape(str(s))}</text>')
    def cell(k,x,y,v,size=18):text(x,y,v,size,f'id="cell-{k}" data-value="{v}"')
    text(42,58,'GameLab / minimax value is unique; the strategy may not be',26,'font-weight="700"')
    text(42,88,'Exact small zero-sum games: row maximizes payoff, column minimizes. No training or payoff sampling.',17,'class="muted"')
    text(42,134,'1 Cyclic scores defeat a single-policy ranking',21,'font-weight="700"')
    a=r['cyclic'];text(65,172,'Column action',15,'class="muted"')
    for j in range(3):text(130+92*j,200,j,16)
    for i,row in enumerate(a['payoffs']):
        text(65,239+55*i,i,16)
        for j,v in enumerate(row):
            x,y=100+92*j,213+55*i;color='#d8ede7' if F(v)>0 else '#f3dfd4' if F(v)<0 else '#ececec'
            out.append(f'<rect x="{x}" y="{y}" width="85" height="47" rx="4" fill="{color}"/>');cell(f'matrix-{i}-{j}',x+31,y+30,v)
    for y,label,key in ((213,'Game value','value'),(254,'Pure row security','row_maximin'),(295,'Pure column security','column_minimax')):
        text(470,y,label,17);cell(key,770,y,a['value'] if key=='value' else a['pure_strategy_controls'][key])
    text(470,337,'Mixed equilibrium: each action has probability 1/3.',17)
    text(470,368,'Both always choose action 0: payoff 0, deviation gap 2.',17)
    text(42,421,'2 Duplicate actions create a continuum of optimal policies',21,'font-weight="700"')
    text(42,450,'Rows 0 and 1 duplicate [1,-1]; row 2 is [-1,1]; row 3 is dominated [-2,-2].',16,'class="muted"')
    d=r['degenerate_rectangular'];p=d['row'];text(60,491,'Row',16,'font-weight="700"');text(170,491,'Attainable probability range',16,'font-weight="700"');text(620,491,'Optimal vertex 0',16,'font-weight="700"');text(835,491,'Optimal vertex 1',16,'font-weight="700"')
    for i,item in enumerate(p['coordinate_ranges']):
        y=533+47*i;text(65,y,i,17);lo,hi=F(item['minimum']),F(item['maximum'])
        out.append(f'<line x1="180" y1="{y-6}" x2="530" y2="{y-6}" stroke="#ddd" stroke-width="8"/>')
        out.append(f'<line id="range-{i}" data-min="{lo}" data-max="{hi}" x1="{180+350*float(lo):.3f}" y1="{y-6}" x2="{180+350*float(hi):.3f}" y2="{y-6}" stroke="#127e71" stroke-width="8"/>')
        for side,value in (('minimum',lo),('maximum',hi)):
            out.append(f'<circle id="range-{i}-{side}" cx="{180+350*float(value):.3f}" cy="{y-6}" r="5" fill="#127e71"/>')
        for k in range(2):cell(f'vertex-{k}-{i}',640+215*k,y,p['optimal_vertices'][k]['strategy'][i])
    text(180,722,'0',14);text(350,722,'1/2',14);text(525,722,'1',14)
    text(42,760,'The full face is p0+p1=1/2, p2=1/2, p3=0. Coordinate ranges are not independent.',17)
    text(42,791,'Representative (vertex average): [1/4,1/4,1/2,0]. No claim that this policy is uniquely preferred.',17)
    text(42,846,'3 Tiny payoff changes can flip the unique optimal action',21,'font-weight="700"')
    text(42,876,'Two row actions, one column action. Before: [0,epsilon]; after: [epsilon,0].',16,'class="muted"')
    f=r['perturbation_flip']
    for x,label in ((52,'epsilon'),(350,'Value change'),(630,'Old pair deviation gap after change')):text(x,920,label,16,'font-weight="700"')
    cell('epsilon',52,953,f['epsilon']);cell('value-change',350,953,f['value_change']);cell('transfer-gap',630,953,f['old_pair_in_changed_game']['duality_gap'])
    text(42,999,'Optimal row policy flips [0,1] to [1,0], despite unchanged value and a 10^-12 entry change.',17)
    text(42,1032,'Value changes by at most epsilon; an old equilibrium pair has deviation gap at most 2*epsilon.',17)
    text(42,1080,'Every active basis, singular/infeasible outcome, slack, optimal vertex and coordinate witness is exported.',16)
    text(42,1120,'Developed finite tables only. No general-sum games, learned opponent, unique-policy or scalability claim.',15,'class="muted"')
    text(42,1150,'Perturbation bounds are deterministic, not confidence intervals for unknown empirical scores.',15,'class="muted"')
    encoded=base64.b64encode(zlib.compress(json.dumps(r,sort_keys=True,separators=(',',':')).encode())).decode()
    out.append('<metadata id="report-zlib-base64">'+encoded+'</metadata></svg>')
    return '\n'.join(out)+'\n'


if __name__=='__main__':
    p=Path(__file__).resolve().parents[1]/'assets/minimax-audit.svg';s=render(demo())
    if sys.argv[1:]==['--check']:
        if p.read_text()!=s:raise SystemExit('SVG differs')
    elif not sys.argv[1:]:p.write_text(s)
    else:raise SystemExit('usage: render_demo.py [--check]')
