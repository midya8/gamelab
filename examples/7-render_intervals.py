"""Reproducible interval audit. Only display coordinates use floats."""
import base64
from fractions import Fraction as F
import html
import json
from pathlib import Path
import sys
import zlib
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from gamelab import interval_demo


def render(r):
    out=['<svg xmlns="http://www.w3.org/2000/svg" width="1120" height="1100" viewBox="0 0 1120 1100">','<rect width="1120" height="1100" fill="#f4f1ed"/><rect x="16" y="16" width="1088" height="1068" rx="18" fill="white"/>','<style>text{font-family:Arial,sans-serif;fill:#292929}.muted{fill:#666}</style>']
    def text(x,y,s,size=17,extra=''):out.append(f'<text x="{x}" y="{y}" font-size="{size}" {extra}>{html.escape(str(s))}</text>')
    def cell(k,x,y,v):text(x,y,v,18,f'id="cell-{k}" data-value="{v}"')
    text(42,58,'GameLab / worst regrets must share one payoff table',26,'font-weight="700"')
    text(42,89,'Exact fixed-policy box audits. Row maximizes; column minimizes. Supplied intervals, not confidence intervals.',17,'class="muted"')
    text(42,137,'1 One uncertain entry makes separate worst deviations incompatible',21,'font-weight="700"')
    s=r['shared_entry_conflict'];c=s['chosen_pair'];text(42,170,'Both policies choose action 0. Only A[0,0] varies from 0 to 2; all other payoffs are 1.',17)
    for offset,tag,key in ((70,'Lower matrix','lower'),(315,'Upper matrix','upper')):
        text(offset,212,tag,16,'font-weight="700"')
        for i,row in enumerate(s[key]):
            for j,v in enumerate(row):
                x,y=offset+68*j,229+48*i;out.append(f'<rect x="{x}" y="{y}" width="61" height="41" rx="4" fill="{("#d8ede7" if (i,j)==(0,0) else "#ececec")}"/>');cell(f'{key}-{i}-{j}',x+24,y+27,v)
    for y,label,key,value in ((241,'Exact shared-table worst gap','shared-gap',c['worst_gap']),(279,'Sum of separate worst deviations','separate',c['sum_separately_maximized_deviations']),(317,'Attainable game-value range width','value-width',s['value_range']['width']),(355,'Robust-security pair worst gap','robust-gap',s['robust_security_pair']['exact_box_audit']['worst_gap'])):
        text(570,y,label,16);cell(key,1015,y,value)
    text(42,400,'A[0,0]',16,'font-weight="700"');text(220,400,'Row deviation gain',16,'font-weight="700"');text(475,400,'Column deviation gain',16,'font-weight="700"');text(800,400,'Joint gap',16,'font-weight="700"')
    # These three direct evaluations are simple controls, computed from the reported fixed strategies.
    x=list(map(F,c['row_strategy']));y=list(map(F,c['column_strategy']))
    for k,t in enumerate((F(0),F(1),F(2))):
        a=[[t,F(1)],[F(1),F(1)]];pay=sum(x[i]*a[i][j]*y[j] for i in range(2) for j in range(2));rg=max(sum(a[i][j]*y[j] for j in range(2)) for i in range(2))-pay;cg=pay-min(sum(x[i]*a[i][j] for i in range(2)) for j in range(2));line=443+43*k
        for xx,key,v in ((65,'entry',t),(285,'row',rg),(560,'column',cg),(835,'gap',rg+cg)):cell(f'probe-{k}-{key}',xx,line,v)
    text(42,580,'Row worst needs A[0,0]=0; column worst needs A[0,0]=2. No single table attains both.',17)
    text(42,613,'The game value is always 1. Lower-game row / upper-game column policies are robust equilibria here.',17)
    text(42,675,'2 A fully variable 2x2 box still has shared-entry cancellation',21,'font-weight="700"')
    text(42,709,'All four entries range from 0 to 1. Both fixed policies mix [1/2,1/2].',17)
    f=r['full_box']['chosen_pair']
    for xx,label,key,v in ((55,'Exact shared worst gap','full-gap',f['worst_gap']),(390,'Separate worst sum','full-separate',f['sum_separately_maximized_deviations']),(750,'Value range width','full-width',r['full_box']['value_range']['width'])):
        text(xx,753,label,16,'font-weight="700"');cell(key,xx+50,790,v)
    text(42,832,'For reply pair (0,0), the coefficient of A[0,0] is 1/2 - 1/2 = 0, not two independent choices.',17)
    text(42,885,'3 A one-action game can have uncertain value but zero exploitability',21,'font-weight="700"')
    one=r['singleton_cancellation'];text(42,922,'Single entry [-50,50]: value range width',17);cell('singleton-width',450,922,one['value_range']['width']);text(580,922,'but every pair gap is',17);cell('singleton-gap',800,922,one['chosen_pair']['worst_gap'])
    text(42,971,'Every pure reply pair retains signed coefficients, endpoint choices, contributions and an attaining matrix.',16)
    text(42,1006,'Endpoint games certify attainable value extrema and separate robust security, not an optimal worst-gap pair.',15,'class="muted"')
    text(42,1037,'No coupled uncertainty, statistical coverage, payoff-estimation or general-sum claim.',15,'class="muted"')
    blob=base64.b64encode(zlib.compress(json.dumps(r,sort_keys=True,separators=(',',':')).encode())).decode();out.append('<metadata id="report-zlib-base64">'+blob+'</metadata></svg>');return '\n'.join(out)+'\n'


if __name__=='__main__':
    p=Path(__file__).resolve().parents[1]/'assets/interval-audit.svg';s=render(interval_demo())
    if sys.argv[1:]==['--check']:
        if p.read_text()!=s:raise SystemExit('SVG differs')
    elif not sys.argv[1:]:p.write_text(s)
    else:raise SystemExit('usage: render_intervals.py [--check]')
