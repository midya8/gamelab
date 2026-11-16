from fractions import Fraction as F
import copy
import itertools
import random
import unittest
from gamelab import path_audit
import json
from pathlib import Path
import subprocess
import sys
import tempfile
ROOT=Path(__file__).resolve().parents[1]


class PolicyPathTests(unittest.TestCase):
    def direct_gap(self,a,x,y):
        return max(sum(F(v)*p for v,p in zip(row,y)) for row in a)-min(sum(x[i]*F(a[i][j]) for i in range(len(x))) for j in range(len(y)))

    def test_matching_pennies_and_restricted_rps(self):
        r=path_audit([[1,-1],[-1,1]],[1,0],[1,0],[0,1],[0,1])
        self.assertEqual(r['minimizing_alpha_interval'],['1/2','1/2']);self.assertEqual(r['minimum_gap'],'0')
        self.assertEqual([p['slope'] for p in r['pieces']],['-4','4'])
        r=path_audit([[0,-1,1],[1,0,-1],[-1,1,0]],[1,0,0],[1,0,0],[0,1,0],[0,1,0])
        self.assertEqual(r['minimizing_alpha_interval'],['2/3','2/3']);self.assertEqual(r['minimum_gap'],'2/3')
        self.assertFalse(r['representative_audit']['is_equilibrium'])
        # The inactive row/column crossing at1/3 is kept, not called a change in the envelope.
        self.assertEqual([k['alpha'] for k in r['knots']],['0','1/3','2/3','1'])
        self.assertEqual(r['pieces'][0]['slope'],r['pieces'][1]['slope'])

    def test_flat_faces_stationary_endpoints_and_one_action(self):
        for a,x0,y0,x1,y1 in [([[0,0],[0,0]],[1,0],[0,1],[0,1],[1,0]),([[7]],[1],[1],[1],[1]),([[2,2]],[1],[1,0],[1],[0,1])]:
            r=path_audit(a,x0,y0,x1,y1);self.assertEqual(r['minimum_gap'],'0');self.assertEqual(r['minimizing_alpha_interval'],['0','1'])
        r=path_audit([[0,2]],[1],[0,1],[1],[1,0]);self.assertEqual(r['minimizing_alpha_interval'],['1','1'])
        r=path_audit([[0,2]],[1],[1,0],[1],[0,1]);self.assertEqual(r['minimizing_alpha_interval'],['0','0'])

    def test_exact_inequality_feasibility_reference(self):
        # Gap<=z iff every reply-pair affine line<=z. Recover its entire feasible
        # alpha interval directly, without production crossings or envelope code.
        rng=random.Random(181);cases=0
        for m,n in [(1,1),(1,3),(3,1),(2,2),(2,3),(3,2),(4,4)]:
            for _ in range(8):
                a=[[rng.randint(-3,3) for _ in range(n)] for _ in range(m)]
                def simplex(k):
                    counts=[rng.randint(0,5) for _ in range(k)]
                    if not sum(counts):counts[0]=1
                    return [F(c,sum(counts)) for c in counts]
                x0,x1,y0,y1=simplex(m),simplex(m),simplex(n),simplex(n)
                r=path_audit(a,x0,y0,x1,y1);z=F(r['minimum_gap']);lo,hi=F(0),F(1)
                pairlines=[]
                for i,j in itertools.product(range(m),range(n)):
                    b=sum(F(a[i][k])*y0[k] for k in range(n))-sum(x0[k]*F(a[k][j]) for k in range(m))
                    end=sum(F(a[i][k])*y1[k] for k in range(n))-sum(x1[k]*F(a[k][j]) for k in range(m));s=end-b;pairlines.append((b,s))
                    if s>0:hi=min(hi,(z-b)/s)
                    elif s<0:lo=max(lo,(z-b)/s)
                    else:self.assertLessEqual(b,z)
                self.assertEqual([lo,hi],list(map(F,r['minimizing_alpha_interval'])))
                # Independent 2D epigraph-vertex enumeration minimizes z over [0,1].
                candidates=[max(b for b,s in pairlines),max(b+s for b,s in pairlines)]
                for (b,s),(c,t) in itertools.combinations(pairlines,2):
                    if s!=t:
                        alpha=(c-b)/(s-t)
                        if 0<=alpha<=1:candidates.append(max(v+w*alpha for v,w in pairlines))
                self.assertEqual(z,min(candidates))
                for alpha in [F(k,8) for k in range(9)]:
                    x=[u+alpha*(v-u) for u,v in zip(x0,x1)];y=[u+alpha*(v-u) for u,v in zip(y0,y1)]
                    gap=self.direct_gap(a,x,y);self.assertGreaterEqual(gap,z)
                    piece=next(p for p in r['pieces'] if F(p['left'])<=alpha<=F(p['right']))
                    self.assertEqual(F(piece['intercept'])+F(piece['slope'])*alpha,gap)
                for k in r['knots']:
                    self.assertEqual(F(k['audit']['duality_gap']),self.direct_gap(a,list(map(F,k['row_strategy'])),list(map(F,k['column_strategy']))))
                cases+=1
        self.assertEqual(cases,56)

    def test_reversal_affine_and_negative_transpose(self):
        a=[[2,-1,3],[0,4,-2]];x0=[1,0];x1=[0,1];y0=[1,0,0];y1=[0,0,1]
        r=path_audit(a,x0,y0,x1,y1);rev=path_audit(a,x1,y1,x0,y0)
        lo,hi=map(F,r['minimizing_alpha_interval']);self.assertEqual(list(map(F,rev['minimizing_alpha_interval'])),[1-hi,1-lo])
        shifted=path_audit([[3*v+7 for v in row] for row in a],x0,y0,x1,y1)
        self.assertEqual(F(shifted['minimum_gap']),3*F(r['minimum_gap']));self.assertEqual(shifted['minimizing_alpha_interval'],r['minimizing_alpha_interval'])
        negt=[[-a[i][j] for i in range(2)] for j in range(3)];swap=path_audit(negt,y0,x0,y1,x1)
        self.assertEqual(swap['minimum_gap'],r['minimum_gap']);self.assertEqual(swap['minimizing_alpha_interval'],r['minimizing_alpha_interval'])

    def test_validation_and_input_rng_output_isolation(self):
        a=[[1,-1],[-1,1]];v=[[1,0],[1,0],[0,1],[0,1]];old=copy.deepcopy((a,v));state=random.getstate();r=path_audit(a,*v)
        self.assertEqual((a,v),old);self.assertEqual(random.getstate(),state);r['row_start'][0]='changed';self.assertEqual((a,v),old)
        for bad in ([True,False],[0,0],[1],[-1,2],[.5,.5],['1/0',0],['1'*161,0],[2**513,0]):
            for endpoint in range(4):
                args=copy.deepcopy(v);args[endpoint]=bad
                with self.assertRaises(ValueError):path_audit(a,*args)
        with self.assertRaises(ValueError):path_audit([[1],[2,3]],*v)

    def test_interior_flat_face_repeated_parallel_and_inactive_lines(self):
        a=[[0,0],[1,-2],[-2,1],[0,0]]
        r=path_audit(a,[1,0,0,0],[1,0],[1,0,0,0],[0,1])
        self.assertEqual(r['minimizing_alpha_interval'],['1/3','2/3'])
        self.assertEqual(r['minimum_gap'],'0');self.assertEqual(r['representative_alpha'],'1/2')
        self.assertTrue(r['representative_audit']['is_equilibrium'])
        self.assertIn({'side':'row','actions':[0,3],'kind':'identical','alpha':None},r['pair_crossings'])
        self.assertEqual([p['slope'] for p in r['pieces']],['-3','0','0','3'])
        r=path_audit([[3,4],[1,2],[-2,1]],[1,0,0],[1,0],[1,0,0],[0,1])
        self.assertIn({'side':'row','actions':[0,1],'kind':'parallel','alpha':None},r['pair_crossings'])
        self.assertIn({'side':'row','actions':[0,2],'kind':'crossing','alpha':'5/2'},r['pair_crossings'])
        self.assertEqual([k['alpha'] for k in r['knots']],['0','1'])

    def test_cli_complete_report_strict_schema_and_resource_limits(self):
        x=dict(schema_version=1,payoffs=[[0,-1,1],[1,0,-1],[-1,1,0]],row_start=[1,0,0],column_start=[1,0,0],row_end=[0,1,0],column_end=[0,1,0])
        expected=path_audit(**{k:v for k,v in x.items() if k!='schema_version'})
        with tempfile.TemporaryDirectory() as d:
            f=Path(d)/'input.json';f.write_text(json.dumps(x))
            p=subprocess.run([sys.executable,'-m','gamelab','path',str(f)],cwd=ROOT,capture_output=True)
            self.assertEqual(p.returncode,0);self.assertEqual(json.loads(p.stdout),expected);self.assertEqual(p.stderr,b'')
            bads=[b'{}',json.dumps(dict(x,schema_version=True)).encode(),json.dumps(dict(x,extra=0)).encode(),json.dumps({k:v for k,v in x.items() if k!='row_end'}).encode(),b'{"schema_version":1,"schema_version":1}',b'NaN',b'\xff',b'['*2000+b']'*2000,b' '*200001,json.dumps(dict(x,row_end=[0.5,0.5,0])).encode(),json.dumps(dict(x,payoffs=[[True]])).encode()]
            for raw in bads:
                f.write_bytes(raw);p=subprocess.run([sys.executable,'-m','gamelab','path',str(f)],cwd=ROOT,capture_output=True)
                self.assertEqual(p.returncode,2,raw[:40]);self.assertEqual(p.stdout,b'');self.assertIn(b'error:',p.stderr);self.assertNotIn(b'Traceback',p.stderr)
