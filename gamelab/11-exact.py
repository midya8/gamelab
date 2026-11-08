"""Small exact inputs and exact elimination, with no floating point tolerance."""
from fractions import Fraction as F
import re


def rational(value,name='value'):
    if isinstance(value,bool) or not isinstance(value,(str,int,F)):
        raise ValueError(name+' must be an exact integer, string or Fraction, never float/bool')
    if isinstance(value,str) and (len(value)>160 or not re.fullmatch(r'-?\d+(?:/\d+|\.\d+)?',value)):
        raise ValueError(name+' has invalid exact syntax')
    try:q=F(value)
    except (ValueError,ZeroDivisionError):raise ValueError(name+' is not rational') from None
    if max(abs(q.numerator).bit_length(),q.denominator.bit_length())>512:
        raise ValueError(name+' exceeds 512-bit input components')
    return q


def matrix(payoffs):
    if not isinstance(payoffs,(list,tuple)) or not 1<=len(payoffs)<=4:
        raise ValueError('payoffs needs 1..4 rows')
    if any(not isinstance(r,(list,tuple)) for r in payoffs):raise ValueError('rows must be sequences')
    n=len(payoffs[0])
    if not 1<=n<=4 or any(len(r)!=n for r in payoffs):raise ValueError('payoffs must be rectangular with 1..4 columns')
    return [[rational(a,'payoff') for a in row] for row in payoffs]


def strategy(values,n):
    if not isinstance(values,(list,tuple)) or len(values)!=n:raise ValueError('strategy shape mismatch')
    x=[rational(v,'probability') for v in values]
    if any(v<0 for v in x) or sum(x)!=1:raise ValueError('probabilities must be nonnegative and sum exactly to one')
    return x


def elimination(a,b):
    """Square exact system. Singular systems return rank, never a guessed solution."""
    n=len(b);r=[list(map(F,row))+[F(v)] for row,v in zip(a,b)]
    pivots=[];det=F(1);rank=0
    for c in range(n):
        p=next((i for i in range(rank,n) if r[i][c]),None)
        if p is None:continue
        if p!=rank:r[p],r[rank]=r[rank],r[p];det=-det
        q=r[rank][c];det*=q;r[rank]=[x/q for x in r[rank]]
        for i in range(n):
            if i!=rank:
                q=r[i][c];r[i]=[x-q*y for x,y in zip(r[i],r[rank])]
        pivots.append(c);rank+=1
    if rank<n:return {'rank':rank,'determinant':F(0),'solution':None,'pivots':pivots}
    x=[row[-1] for row in r]
    assert all(sum(v*w for v,w in zip(row,x))==v for row,v in zip(a,b))
    return {'rank':rank,'determinant':det,'solution':x,'pivots':pivots}


def jsonify(value):
    if isinstance(value,F):return str(value)
    if isinstance(value,dict):return {k:jsonify(v) for k,v in value.items()}
    if isinstance(value,(tuple,list)):return [jsonify(v) for v in value]
    return value
