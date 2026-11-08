"""Exhaustive small security-LP vertices, not a scalable or general-sum solver."""
from fractions import Fraction as F
from itertools import combinations
from math import comb
from .exact import matrix,strategy,elimination,jsonify


def _security(a):
    """Row maximizes v, p>=0,sum p=1 and p^T A[:,j]-v>=0."""
    m,n=len(a),len(a[0])
    inequalities=[]
    for i in range(m):inequalities.append({'label':'probability_'+str(i),'coefficients':[F(int(i==k)) for k in range(m)]+[F(0)]})
    for j in range(n):inequalities.append({'label':'opponent_'+str(j),'coefficients':[a[i][j] for i in range(m)]+[F(-1)]})
    total=comb(m+n,m);attempts=[];vertices={}
    for basis in combinations(range(m+n),m):
        eq=[[F(1)]*m+[F(0)]]+[inequalities[i]['coefficients'] for i in basis]
        rhs=[F(1)]+[F(0)]*m;answer=elimination(eq,rhs)
        row={'basis':list(basis),'basis_labels':[inequalities[i]['label'] for i in basis],**answer}
        if answer['solution'] is None:row['status']='singular'
        else:
            x=answer['solution'];slacks=[sum(v*w for v,w in zip(r['coefficients'],x)) for r in inequalities]
            row['slacks']=slacks;row['violated']=[i for i,s in enumerate(slacks) if s<0]
            row['status']='infeasible' if row['violated'] else 'feasible'
            if not row['violated']:
                key=tuple(x)
                if key not in vertices:vertices[key]={'strategy':x[:-1],'value':x[-1],'slacks':slacks,'active':[i for i,s in enumerate(slacks) if not s],'bases':[]}
                vertices[key]['bases'].append(list(basis))
        attempts.append(row)
    assert vertices and len(attempts)==total
    all_vertices=sorted(vertices.values(),key=lambda x:tuple(x['strategy'])+(x['value'],))
    v=max(x['value'] for x in all_vertices);optimal=[x for x in all_vertices if x['value']==v]
    centroid=[sum(x['strategy'][i] for x in optimal)/len(optimal) for i in range(m)]
    ranges=[]
    for i in range(m):
        lo=min(x['strategy'][i] for x in optimal);hi=max(x['strategy'][i] for x in optimal)
        ranges.append({'coordinate':i,'minimum':lo,'maximum':hi,
                       'minimum_vertex':next(k for k,x in enumerate(optimal) if x['strategy'][i]==lo),
                       'maximum_vertex':next(k for k,x in enumerate(optimal) if x['strategy'][i]==hi)})
    return {'value':v,'representative':centroid,'representative_rule':'equal average of all distinct optimal vertices',
            'unique_optimal_strategy':len(optimal)==1,'optimal_vertices':optimal,'coordinate_ranges':ranges,
            'inequalities':inequalities,'vertices':all_vertices,'attempts':attempts,
            'basis_budget':total,'feasible_basis_count':sum(r['status']=='feasible' for r in attempts),
            'singular_basis_count':sum(r['status']=='singular' for r in attempts),
            'scope':'convex hull of optimal vertices is the full optimal strategy set; coordinate ranges alone are not that set'}


def _audit(a,x,y):
    row=[sum(a[i][j]*y[j] for j in range(len(y))) for i in range(len(x))]
    col=[sum(x[i]*a[i][j] for i in range(len(x))) for j in range(len(y))]
    p=sum(x[i]*row[i] for i in range(len(x)));upper=max(row);lower=min(col)
    rr=upper-p;cr=p-lower
    assert rr>=0 and cr>=0
    return {'payoff':p,'row_pure_payoffs':row,'column_pure_payoffs':col,
            'row_best_replies':[i for i,v in enumerate(row) if v==upper],
            'column_best_replies':[j for j,v in enumerate(col) if v==lower],
            'row_deviation_gain':rr,'column_deviation_gain':cr,
            'lower_security':lower,'upper_security':upper,'duality_gap':upper-lower,
            'gap_equals_sum_deviation_gains':upper-lower==rr+cr,
            'is_equilibrium':upper==lower}


def _solve(a):
    m,n=len(a),len(a[0]);row=_security(a)
    # Column maximizes its negative payoff in the transposed game. Translate signs.
    col=_security([[-a[i][j] for i in range(m)] for j in range(n)])
    assert row['value']==-col['value']
    v=row['value'];x=row['representative'];y=col['representative'];check=_audit(a,x,y)
    assert check['is_equilibrium'] and check['payoff']==v
    rslack=[v-p for p in check['row_pure_payoffs']];cslack=[p-v for p in check['column_pure_payoffs']]
    assert all(s>=0 for s in rslack+cslack)
    assert all(p*s==0 for p,s in zip(x,rslack)) and all(p*s==0 for p,s in zip(y,cslack))
    return {'schema_version':1,'payoffs':a,'rows':m,'columns':n,'value':v,
            'row':row,'column_negative_game':col,'equilibrium_audit':check,
            'certificate':{'primal_value':v,'dual_value':-col['value'],'duality_gap':F(0),
                'row_probability_sum':sum(x),'column_probability_sum':sum(y),
                'row_slacks':rslack,'column_slacks':cslack,
                'row_complementarity_products':[p*s for p,s in zip(x,rslack)],
                'column_complementarity_products':[p*s for p,s in zip(y,cslack)]},
            'pure_strategy_controls':{'row_maximin':max(min(r) for r in a),
                                      'column_minimax':min(max(a[i][j] for i in range(m)) for j in range(n)),
                                      'saddles':[[i,j] for i in range(m) for j in range(n) if a[i][j]==min(a[i]) and a[i][j]==max(a[k][j] for k in range(m))]},
            'scope':'supplied finite zero-sum payoff matrix only; row maximizes, column minimizes; no general-sum or empirical payoff guarantee'}


def solve(payoffs):return jsonify(_solve(matrix(payoffs)))


def audit(payoffs,row_strategy,column_strategy):
    a=matrix(payoffs);x=strategy(row_strategy,len(a));y=strategy(column_strategy,len(a[0]));sol=_solve(a);v=sol['value'];check=_audit(a,x,y)
    check.update({'schema_version':1,'payoffs':a,'row_strategy':x,'column_strategy':y,'game_value':v,
                  'row_exploitability':v-check['lower_security'],
                  'column_exploitability':check['upper_security']-v,
                  'scope':'sum convention: pair exploitability equals sum of each player security loss, not half this sum'})
    assert check['duality_gap']==check['row_exploitability']+check['column_exploitability']
    return jsonify(check)


def perturbation(original,changed):
    a,b=matrix(original),matrix(changed)
    if len(a)!=len(b) or len(a[0])!=len(b[0]):raise ValueError('perturbation matrices must have matching shapes')
    delta=[[v-u for u,v in zip(ar,br)] for ar,br in zip(a,b)];eps=max(abs(v) for row in delta for v in row)
    old,new=_solve(a),_solve(b);x=old['row']['representative'];y=old['column_negative_game']['representative']
    check=_audit(b,x,y);value_shift=new['value']-old['value']
    rex=new['value']-check['lower_security'];cex=check['upper_security']-new['value']
    assert abs(value_shift)<=eps and rex<=2*eps and cex<=2*eps and check['duality_gap']<=2*eps
    witnesses=[[i,j] for i,row in enumerate(delta) for j,v in enumerate(row) if abs(v)==eps]
    return jsonify({'schema_version':1,'original':old,'changed':new,'entry_changes':delta,'epsilon':eps,
                    'epsilon_witness_entries':witnesses,'value_change':value_shift,
                    'value_shift_slack':eps-abs(value_shift),'old_pair_in_changed_game':check,
                    'row_transfer_exploitability':rex,'column_transfer_exploitability':cex,
                    'individual_transfer_bound':2*eps,'pair_transfer_bound':2*eps,
                    'row_transfer_slack':2*eps-rex,'column_transfer_slack':2*eps-cex,
                    'pair_transfer_slack':2*eps-check['duality_gap'],
                    'scope':'deterministic entrywise perturbation only, not statistical uncertainty; strategy coordinates need not change continuously'})
