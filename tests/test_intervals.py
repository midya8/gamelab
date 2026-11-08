import copy
from fractions import Fraction as F
from itertools import product
import json
from pathlib import Path
import random
import subprocess
import sys
import tempfile
import unittest
from gamelab import interval_audit,interval_demo,solve
ROOT=Path(__file__).resolve().parents[1]


def vertices(lo,hi):
    m,n=len(lo),len(lo[0])
    for bits in product((0,1),repeat=m*n):yield [[F(hi[i][j] if bits[i*n+j] else lo[i][j]) for j in range(n)] for i in range(m)]


def direct(a,x,y):
    row=[sum(a[i][j]*y[j] for j in range(len(y))) for i in range(len(x))]
    col=[sum(x[i]*a[i][j] for i in range(len(x))) for j in range(len(y))]
    p=sum(x[i]*row[i] for i in range(len(x)))
    return max(row)-min(col),max(row)-p,p-min(col),p


class IntervalTests(unittest.TestCase):
    def test_shared_entry_incompatible_deviation_maxima(self):
        r=interval_demo()['shared_entry_conflict'];c=r['chosen_pair']
        self.assertEqual(c['worst_gap'],'1');self.assertEqual(c['sum_separately_maximized_deviations'],'2');self.assertEqual(c['separate_deviation_conservatism'],'1')
        self.assertEqual(c['row_deviations'][1]['attaining_matrix'][0][0],'0');self.assertEqual(c['column_deviations'][1]['attaining_matrix'][0][0],'2')
        self.assertEqual(r['value_range']['minimum'],'1');self.assertEqual(r['value_range']['maximum'],'1');self.assertEqual(r['robust_security_pair']['exact_box_audit']['worst_gap'],'0')
    def test_singleton_shared_payoff_cancels(self):
        r=interval_demo()['singleton_cancellation'];c=r['chosen_pair'];self.assertEqual(c['worst_gap'],'0');self.assertEqual(c['separate_security_bound'],'100');self.assertEqual(c['reply_pairs'][0]['coefficients'],[['0']]);self.assertEqual(c['reply_pairs'][0]['endpoint_choices'],[['free']]);self.assertEqual(r['value_range']['width'],'100')
    def test_full_box_uniform_exact_joint_is_half_loose(self):
        c=interval_demo()['full_box']['chosen_pair'];self.assertEqual(c['worst_gap'],'1/2');self.assertEqual(c['sum_separately_maximized_deviations'],'1');self.assertEqual(c['maximizing_reply_pair_indices'],list(range(4)))
        self.assertEqual(c['reply_pairs'][0]['coefficients'],[['0','1/2'],['-1/2','0']]);self.assertEqual(c['reply_pairs'][0]['attaining_matrix'],[['0','1'],['0','0']])
    def test_16_boxes_9_pairs_exhaustive_endpoint_reference(self):
        base=[[F(0),F(-1)],[F(2),F(0)]]
        for widths in product((0,1),repeat=4):
            hi=[[base[i][j]+widths[2*i+j] for j in range(2)] for i in range(2)];corners=list(vertices(base,hi))
            for p,q in product((F(0),F(1,2),F(1)),repeat=2):
                x=[p,1-p];y=[q,1-q];c=interval_audit(base,hi,x,y)['chosen_pair'];ref=[direct(a,x,y) for a in corners]
                self.assertEqual(F(c['worst_gap']),max(r[0] for r in ref));self.assertEqual(F(c['worst_row_deviation']),max(r[1] for r in ref));self.assertEqual(F(c['worst_column_deviation']),max(r[2] for r in ref));self.assertEqual(F(c['payoff_range']['minimum']),min(r[3] for r in ref));self.assertEqual(F(c['payoff_range']['maximum']),max(r[3] for r in ref))
    def test_every_signed_support_and_attainment(self):
        r=interval_audit([[-2,'1/4'],[0,-1]],[[3,2],['7/3',1]],['1/3','2/3'],['3/4','1/4']);c=r['chosen_pair'];lo=r['lower'];hi=r['upper']
        for w in c['reply_pairs']+c['row_deviations']+c['column_deviations']:
            total=F(0)
            for i in range(2):
                for j in range(2):
                    v=F(w['coefficients'][i][j]);b=F(w['attaining_matrix'][i][j]);l,h=F(lo[i][j]),F(hi[i][j]);self.assertTrue(l<=b<=h);self.assertEqual(b,h if v>0 else l);self.assertEqual(F(w['terms'][i][j]),v*b);total+=v*b
            self.assertEqual(total,F(w['maximum']))
            for a in vertices(lo,hi):self.assertLessEqual(sum(F(w['coefficients'][i][j])*a[i][j] for i in range(2) for j in range(2)),total)
        self.assertEqual(direct([[F(v) for v in row] for row in c['attaining_matrix']],[F(1,3),F(2,3)],[F(3,4),F(1,4)])[0],F(c['worst_gap']))
    def test_attainable_value_extrema_all_corners(self):
        lo=[[-1,0],[2,-2]];hi=[[2,1],[3,0]];r=interval_audit(lo,hi,['1/2']*2,['1/2']*2);values=[F(solve(a)['value']) for a in vertices(lo,hi)]
        self.assertEqual(F(r['value_range']['minimum']),min(values));self.assertEqual(F(r['value_range']['maximum']),max(values));self.assertEqual(r['value_range']['minimum_matrix'],r['lower']);self.assertEqual(r['value_range']['maximum_matrix'],r['upper'])
    def test_robust_security_pair_at_every_corner(self):
        lo=[[-1,0],[2,-2]];hi=[[2,1],[3,0]];r=interval_audit(lo,hi,['1/2']*2,['1/2']*2);b=r['robust_security_pair'];x=list(map(F,b['row_strategy']));y=list(map(F,b['column_strategy']));floor=F(b['row_security_floor']);ceiling=F(b['column_security_ceiling'])
        self.assertEqual(floor,F(r['lower_game']['value']));self.assertEqual(ceiling,F(r['upper_game']['value']))
        for a in vertices(lo,hi):
            self.assertGreaterEqual(min(sum(x[i]*a[i][j] for i in range(2)) for j in range(2)),floor);self.assertLessEqual(max(sum(a[i][j]*y[j] for j in range(2)) for i in range(2)),ceiling);self.assertLessEqual(direct(a,x,y)[0],F(b['gap_upper_bound']))
    def test_zero_width_recovers_fixed_game(self):
        a=[[3,0],[1,2]];r=interval_audit(a,a,[1,0],[1,0]);self.assertEqual(r['value_range']['width'],'0');self.assertEqual(r['robust_security_pair']['exact_box_audit']['worst_gap'],'0');self.assertEqual(r['chosen_pair']['worst_gap'],'3')
    def test_affine_translation_and_scale(self):
        lo=[[-1,0],[2,-2]];hi=[[2,1],[3,0]];x=['1/3','2/3'];y=['3/4','1/4'];a=interval_audit(lo,hi,x,y);b=interval_audit([[3*v+7 for v in row] for row in lo],[[3*v+7 for v in row] for row in hi],x,y)
        self.assertEqual(F(b['chosen_pair']['worst_gap']),3*F(a['chosen_pair']['worst_gap']));self.assertEqual(F(b['value_range']['minimum']),3*F(a['value_range']['minimum'])+7);self.assertEqual(F(b['value_range']['maximum']),3*F(a['value_range']['maximum'])+7)
    def test_four_by_four_and_rectangular(self):
        r=interval_audit([[0]*4]*4,[[1]*4]*4,['1/4']*4,['1/4']*4);self.assertEqual(len(r['chosen_pair']['reply_pairs']),16);self.assertEqual(r['chosen_pair']['worst_gap'],'3/4')
        s=interval_audit([[0,1,2]],[[1,3,4]],[1],['1/3']*3);ref=max(direct(a,[F(1)],[F(1,3)]*3)[0] for a in vertices(s['lower'],s['upper']));self.assertEqual(F(s['chosen_pair']['worst_gap']),ref)
    def test_no_mutation_or_rng(self):
        lo=[[0,1],[1,1]];hi=[[2,1],[1,1]];x=[1,0];y=[1,0];before=copy.deepcopy((lo,hi,x,y));state=random.getstate();interval_audit(lo,hi,x,y);self.assertEqual(before,(lo,hi,x,y));self.assertEqual(state,random.getstate())
    def test_invalid_inputs(self):
        cases=[([[0]],[[0,1]],[1],[1]),([[1]],[[0]],[1],[1]),([[0]],[[1]],[0],[1]),([[0]],[[1]],[1],[True]),([[0.0]],[[1]],[1],[1]),([[0]],[[1]],[1,0],[1])]
        for args in cases:
            with self.assertRaises(ValueError):interval_audit(*args)
    def test_cli_complete_outputs_and_errors(self):
        p=subprocess.run([sys.executable,'-m','gamelab','interval-demo'],cwd=ROOT,capture_output=True);self.assertEqual(p.returncode,0);self.assertEqual(json.loads(p.stdout),interval_demo())
        p=subprocess.run([sys.executable,'-m','gamelab','intervals',str(ROOT/'examples/intervals-input.json')],cwd=ROOT,capture_output=True);self.assertEqual(p.returncode,0);self.assertEqual(json.loads(p.stdout),interval_demo()['shared_entry_conflict'])
        with tempfile.TemporaryDirectory() as d:
            f=Path(d)/'bad.json'
            for raw in ('{}','{"schema_version":1,"lower":[[0]],"upper":[[1]],"row_strategy":[1],"column_strategy":[1],"extra":0}','{"schema_version":1,"schema_version":1}', '{"schema_version":1,"lower":[[1]],"upper":[[0]],"row_strategy":[1],"column_strategy":[1]}'):
                f.write_text(raw);p=subprocess.run([sys.executable,'-m','gamelab','intervals',str(f)],cwd=ROOT,capture_output=True);self.assertEqual(p.returncode,2);self.assertEqual(p.stdout,b'');self.assertIn(b'error:',p.stderr)
