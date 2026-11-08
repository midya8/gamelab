"""Fixed-policy support-function certificates for a supplied Cartesian payoff box."""
from fractions import Fraction as F
from .exact import matrix,strategy,jsonify
from .core import _solve,_audit


def _support(lo,hi,c):
    witness=[];choices=[];terms=[]
    for lr,hr,cr in zip(lo,hi,c):
        witness.append([h if w>0 else l for l,h,w in zip(lr,hr,cr)])
        choices.append(['upper' if w>0 else 'lower' if w<0 else 'free' for w in cr])
        terms.append([w*(h if w>0 else l) for l,h,w in zip(lr,hr,cr)])
    return {'coefficients':c,'endpoint_choices':choices,'attaining_matrix':witness,
            'terms':terms,'maximum':sum((sum(r) for r in terms),F(0))}


def _fixed(lo,hi,x,y):
    m,n=len(x),len(y);pairs=[];rows=[];cols=[]
    for i in range(m):
        c=[[(F(int(k==i))-x[k])*y[l] for l in range(n)] for k in range(m)]
        s=_support(lo,hi,c);s['reply']=i;rows.append(s)
        for j in range(n):
            c=[[F(int(k==i))*y[l]-x[k]*int(l==j) for l in range(n)] for k in range(m)]
            s=_support(lo,hi,c);s.update({'row_reply':i,'column_reply':j});pairs.append(s)
    for j in range(n):
        c=[[x[k]*(y[l]-F(int(l==j))) for l in range(n)] for k in range(m)]
        s=_support(lo,hi,c);s['reply']=j;cols.append(s)
    worst=max(s['maximum'] for s in pairs);rp=max(s['maximum'] for s in rows);cp=max(s['maximum'] for s in cols)
    winners=[i for i,s in enumerate(pairs) if s['maximum']==worst];w=pairs[winners[0]]['attaining_matrix'];check=_audit(w,x,y)
    assert check['duality_gap']==worst and rp>=0 and cp>=0 and worst>=0
    separate=max(sum(hi[i][j]*y[j] for j in range(n)) for i in range(m))-min(sum(x[i]*lo[i][j] for i in range(m)) for j in range(n))
    assert worst<=rp+cp and worst<=separate
    return {'row_strategy':x,'column_strategy':y,'reply_pairs':pairs,'worst_gap':worst,
            'maximizing_reply_pair_indices':winners,'attaining_matrix':w,'attaining_matrix_audit':check,
            'row_deviations':rows,'column_deviations':cols,
            'worst_row_deviation':rp,'worst_column_deviation':cp,
            'maximizing_row_deviation_indices':[i for i,s in enumerate(rows) if s['maximum']==rp],
            'maximizing_column_deviation_indices':[i for i,s in enumerate(cols) if s['maximum']==cp],
            'sum_separately_maximized_deviations':rp+cp,'separate_deviation_conservatism':rp+cp-worst,
            'separate_security_bound':separate,'separate_security_slack':separate-worst,
            'payoff_range':{'minimum':sum(x[i]*lo[i][j]*y[j] for i in range(m) for j in range(n)),
                            'maximum':sum(x[i]*hi[i][j]*y[j] for i in range(m) for j in range(n)),
                            'minimum_matrix':lo,'maximum_matrix':hi}}


def interval_audit(lower,upper,row_strategy,column_strategy):
    lo,hi=matrix(lower),matrix(upper)
    if len(lo)!=len(hi) or len(lo[0])!=len(hi[0]):raise ValueError('interval matrices must have matching shapes')
    if any(l>h for lr,hr in zip(lo,hi) for l,h in zip(lr,hr)):raise ValueError('interval lower exceeds upper')
    m,n=len(lo),len(lo[0]);x=strategy(row_strategy,m);y=strategy(column_strategy,n)
    low,high=_solve(lo),_solve(hi);vlow,vhigh=low['value'],high['value'];assert vlow<=vhigh
    rx=low['row']['representative'];cy=high['column_negative_game']['representative']
    robust=_fixed(lo,hi,rx,cy);width=vhigh-vlow;assert robust['worst_gap']<=width
    lower_columns=[sum(rx[i]*lo[i][j] for i in range(m)) for j in range(n)]
    upper_rows=[sum(hi[i][j]*cy[j] for j in range(n)) for i in range(m)]
    return jsonify({'schema_version':1,'lower':lo,'upper':hi,'rows':m,'columns':n,
        'lower_game':low,'upper_game':high,
        'value_range':{'minimum':vlow,'maximum':vhigh,'width':width,
                       'minimum_matrix':lo,'maximum_matrix':hi},
        'chosen_pair':_fixed(lo,hi,x,y),
        'robust_security_pair':{'row_strategy':rx,'column_strategy':cy,
            'lower_column_payoffs':lower_columns,'upper_row_payoffs':upper_rows,
            'row_security_floor':min(lower_columns),'column_security_ceiling':max(upper_rows),
            'gap_upper_bound':width,'exact_box_audit':robust,'bound_slack':width-robust['worst_gap'],
            'scope':'separate worst-security optimizers, not a minimizer of worst joint pair gap'},
        'scope':'deterministic full Cartesian entrywise intervals only; a single shared matrix per gap; no statistical coverage or coupled uncertainty constraints'})


def interval_demo():
    return {'schema_version':1,
        'shared_entry_conflict':interval_audit([[0,1],[1,1]],[[2,1],[1,1]],[1,0],[1,0]),
        'singleton_cancellation':interval_audit([[-50]],[[50]],[1],[1]),
        'full_box':interval_audit([[0,0],[0,0]],[[1,1],[1,1]],['1/2','1/2'],['1/2','1/2']),
        'scope':'developed deterministic interval fixtures only; no sampled score uncertainty or robust policy superiority claim'}
