"""Exact duality gap along a prescribed independent-policy interpolation path."""
from fractions import Fraction as F
from .exact import matrix, strategy, jsonify
from .core import _audit


def path_audit(payoffs, row_start, column_start, row_end, column_end):
    """Audit a one-dimensional segment, not an equilibrium solver or training path."""
    a=matrix(payoffs);m,n=len(a),len(a[0])
    x0=strategy(row_start,m);x1=strategy(row_end,m)
    y0=strategy(column_start,n);y1=strategy(column_end,n)
    row_lines=[(sum(a[i][j]*y0[j] for j in range(n)),
                sum(a[i][j]*(y1[j]-y0[j]) for j in range(n))) for i in range(m)]
    column_lines=[(sum(x0[i]*a[i][j] for i in range(m)),
                   sum((x1[i]-x0[i])*a[i][j] for i in range(m))) for j in range(n)]
    crossings=[];points={F(0),F(1)}
    for side,lines in [('row',row_lines),('column',column_lines)]:
        for i in range(len(lines)):
            for j in range(i+1,len(lines)):
                b,s=lines[i];c,t=lines[j]
                if s==t:
                    crossings.append(dict(side=side,actions=[i,j],kind='identical' if b==c else 'parallel',alpha=None))
                else:
                    alpha=(c-b)/(s-t)
                    crossings.append(dict(side=side,actions=[i,j],kind='crossing',alpha=alpha))
                    if 0<alpha<1:points.add(alpha)
    points=sorted(points)
    def policies(alpha):return ([u+alpha*(v-u) for u,v in zip(x0,x1)],
                                 [u+alpha*(v-u) for u,v in zip(y0,y1)])
    knots=[]
    for alpha in points:
        x,y=policies(alpha);knots.append(dict(alpha=alpha,row_strategy=x,column_strategy=y,audit=_audit(a,x,y)))
    pieces=[]
    for left,right in zip(points,points[1:]):
        mid=(left+right)/2;x,y=policies(mid);audit=_audit(a,x,y)
        i=audit['row_best_replies'][0];j=audit['column_best_replies'][0]
        intercept=row_lines[i][0]-column_lines[j][0];slope=row_lines[i][1]-column_lines[j][1]
        assert intercept+slope*mid==audit['duality_gap']
        pieces.append(dict(left=left,right=right,intercept=intercept,slope=slope,
                           interior_row_best_replies=audit['row_best_replies'],
                           interior_column_best_replies=audit['column_best_replies']))
    minimum=min(k['audit']['duality_gap'] for k in knots)
    attaining=[k['alpha'] for k in knots if k['audit']['duality_gap']==minimum]
    lo,hi=min(attaining),max(attaining)
    assert all(pieces[i]['slope']<=pieces[i+1]['slope'] for i in range(len(pieces)-1))
    if lo<hi:assert all(p['slope']==0 for p in pieces if lo<=p['left'] and p['right']<=hi)
    x,y=policies((lo+hi)/2);check=_audit(a,x,y);assert check['duality_gap']==minimum
    return jsonify(dict(schema_version=1,payoffs=a,row_start=x0,row_end=x1,column_start=y0,column_end=y1,
        row_payoff_lines=[dict(intercept=b,slope=s) for b,s in row_lines],
        column_payoff_lines=[dict(intercept=b,slope=s) for b,s in column_lines],
        pair_crossings=crossings,knots=knots,pieces=pieces,minimum_gap=minimum,
        minimizing_alpha_interval=[lo,hi],representative_alpha=(lo+hi)/2,
        representative_row_strategy=x,representative_column_strategy=y,representative_audit=check,
        scope='exact one-dimensional supplied independent-policy segment only; not a global gap minimizer, correlated mixture, learned trajectory or finite-step improvement guarantee'))
