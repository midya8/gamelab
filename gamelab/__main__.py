import json
from pathlib import Path
import sys
from . import solve,audit,perturbation,demo,interval_audit,interval_demo


def pairs(items):
    d={}
    for k,v in items:
        if k in d:raise ValueError('duplicate JSON key')
        d[k]=v
    return d


def main():
    try:
        args=sys.argv[1:]
        if args==['demo']:result=demo()
        elif args==['interval-demo']:result=interval_demo()
        elif len(args)==2 and args[0] in ('solve','audit','perturbation','intervals'):
            raw=Path(args[1]).read_bytes()
            if len(raw)>200000:raise ValueError('input exceeds 200000 bytes')
            x=json.loads(raw.decode('utf-8'),object_pairs_hook=pairs,parse_constant=lambda _:(_ for _ in ()).throw(ValueError('nonfinite JSON')))
            if not isinstance(x,dict) or type(x.get('schema_version')) is not int or x['schema_version']!=1:raise ValueError('schema_version must be integer one')
            required={'solve':{'payoffs'},'audit':{'payoffs','row_strategy','column_strategy'},'perturbation':{'original','changed'},'intervals':{'lower','upper','row_strategy','column_strategy'}}[args[0]]
            if set(x)!=required|{'schema_version'}:raise ValueError('input schema mismatch')
            if args[0]=='solve':result=solve(x['payoffs'])
            elif args[0]=='audit':result=audit(x['payoffs'],x['row_strategy'],x['column_strategy'])
            elif args[0]=='perturbation':result=perturbation(x['original'],x['changed'])
            else:result=interval_audit(x['lower'],x['upper'],x['row_strategy'],x['column_strategy'])
        else:raise ValueError('usage: python -m gamelab demo | solve FILE | audit FILE | perturbation FILE | intervals FILE | interval-demo')
        print(json.dumps(result,sort_keys=True,indent=2));return 0
    except (ValueError,OSError,RecursionError) as exc:
        print('error: '+str(exc),file=sys.stderr);return 2
if __name__=='__main__':sys.exit(main())
