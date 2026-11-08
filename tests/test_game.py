import copy
from fractions import Fraction as F
from itertools import product,permutations
import json
from math import comb
from pathlib import Path
import random
import subprocess
import sys
import tempfile
import unittest
from gamelab import solve,audit,perturbation,demo
from gamelab.exact import rational,elimination
ROOT=Path(__file__).resolve().parents[1]


def determinant(a):
    n=len(a);total=F(0)
    for perm in permutations(range(n)):
        v=F((-1)**sum(perm[i]>perm[j] for i in range(n) for j in range(i+1,n)))
        for i,j in enumerate(perm):v*=F(a[i][j])
        total+=v
    return total


def direct(a,x,y):
    a=[[F(v) for v in r] for r in a];x=list(map(F,x));y=list(map(F,y))
    rows=[sum(v*w for v,w in zip(r,y)) for r in a]
    cols=[sum(x[i]*a[i][j] for i in range(len(x))) for j in range(len(y))]
    return rows,cols,sum(x[i]*rows[i] for i in range(len(x)))


class ExactGameTests(unittest.TestCase):
    def test_matching_pennies(self):
        x=solve([[1,-1],[-1,1]]);self.assertEqual(x['value'],'0');self.assertEqual(x['row']['representative'],['1/2','1/2']);self.assertTrue(x['row']['unique_optimal_strategy']);self.assertEqual(x['pure_strategy_controls']['saddles'],[])
    def test_cyclic(self):
        x=demo()['cyclic'];self.assertEqual(x['row']['representative'],['1/3']*3);self.assertEqual(x['value'],'0');self.assertEqual(x['pure_strategy_controls']['row_maximin'],'-1');self.assertEqual(x['pure_strategy_controls']['column_minimax'],'1')
    def test_nonzero_value(self):
        x=solve([[3,0],[1,2]]);self.assertEqual(x['value'],'3/2');self.assertEqual(x['row']['representative'],['1/4','3/4']);self.assertEqual(x['column_negative_game']['representative'],['1/2','1/2'])
    def test_degenerate_full_face(self):
        x=demo()['degenerate_rectangular'];vs=x['row']['optimal_vertices']
        self.assertEqual([v['strategy'] for v in vs],[['0','1/2','1/2','0'],['1/2','0','1/2','0']])
        self.assertFalse(x['row']['unique_optimal_strategy']);self.assertEqual(x['row']['representative'],['1/4','1/4','1/2','0'])
        self.assertTrue(x['row']['singular_basis_count']>0)
        # Coordinate ranges do not authorize independent coordinates: p0+p1=1/2.
        invalid=audit(x['payoffs'],['1/2','1/2',0,0],['1/2','1/2']);self.assertGreater(F(invalid['row_exploitability']),0)
    def test_constant_game_simplex_faces(self):
        x=solve([[2,2,2],[2,2,2]]);self.assertEqual(x['value'],'2');self.assertEqual(len(x['row']['optimal_vertices']),2);self.assertEqual(len(x['column_negative_game']['optimal_vertices']),3)
        self.assertEqual(x['row']['representative'],['1/2','1/2']);self.assertEqual(x['column_negative_game']['representative'],['1/3']*3)
    def test_pure_saddle(self):
        x=solve([[3,2],[1,0]]);self.assertEqual(x['value'],'2');self.assertEqual(x['pure_strategy_controls']['saddles'],[[0,1]]);self.assertEqual(x['row']['representative'],['1','0']);self.assertEqual(x['column_negative_game']['representative'],['0','1'])
    def test_singleton(self):
        x=solve([['-7/3']]);self.assertEqual(x['value'],'-7/3');self.assertEqual(x['row']['representative'],['1']);self.assertEqual(x['column_negative_game']['value'],'7/3')
    def test_single_row_column(self):
        a=solve([[3,-2,1]]);b=solve([[3],[-2],[1]])
        self.assertEqual(a['value'],'-2');self.assertEqual(b['value'],'3');self.assertEqual(a['column_negative_game']['representative'],['0','1','0']);self.assertEqual(b['row']['representative'],['1','0','0'])
    def test_all_81_two_by_two_independent_envelope(self):
        for vals in product((-1,0,1),repeat=4):
            a,b,c,d=map(F,vals);matrix=[[a,b],[c,d]];candidates={F(0),F(1)}
            den=a-b-c+d
            if den:
                p=(d-c)/den
                if 0<=p<=1:candidates.add(p)
            values={p:min(p*a+(1-p)*c,p*b+(1-p)*d) for p in candidates};v=max(values.values());optimal=sorted(p for p in candidates if values[p]==v)
            x=solve(matrix);self.assertEqual(F(x['value']),v)
            # For a concave 1D piecewise-linear envelope, these candidates contain all extremal maximizers.
            self.assertEqual(sorted(F(r['strategy'][0]) for r in x['row']['optimal_vertices']),sorted(set((optimal[0],optimal[-1]))))
            self.assertLessEqual(max(min(r) for r in matrix),v);self.assertGreaterEqual(min(max(a,c),max(b,d)),v)
    def test_every_basis_determinant_residual_and_dedup(self):
        matrices=[[[3,0],[1,2]],[[1,-1],[1,-1],[-1,1],[-2,-2]],[[0,-1,1],[1,0,-1],[-1,1,0]],[[2,2],[2,2]]]
        for a in matrices:
            x=solve(a)
            for key in ('row','column_negative_game'):
                s=x[key];m=len(s['representative']);ineq=s['inequalities'];self.assertEqual(s['basis_budget'],comb(len(ineq),m));feasible=set()
                for attempt in s['attempts']:
                    eq=[[F(1)]*m+[F(0)]]+[[F(v) for v in ineq[i]['coefficients']] for i in attempt['basis']]
                    det=determinant(eq);self.assertEqual(F(attempt['determinant']),det)
                    if det==0:self.assertEqual(attempt['status'],'singular');self.assertIsNone(attempt['solution']);continue
                    sol=list(map(F,attempt['solution']));self.assertEqual(sum(sol[:-1]),1)
                    for row in eq[1:]:self.assertEqual(sum(v*w for v,w in zip(row,sol)),0)
                    slack=[sum(F(v)*w for v,w in zip(row['coefficients'],sol)) for row in ineq];self.assertEqual(list(map(F,attempt['slacks'])),slack)
                    self.assertEqual(attempt['violated'],[i for i,s in enumerate(slack) if s<0])
                    if min(slack)>=0:feasible.add(tuple(sol))
                self.assertEqual(feasible,{tuple(map(F,v['strategy']+[v['value']])) for v in s['vertices']})
    def test_every_optimal_vertex_pair_and_complementarity(self):
        x=demo()['degenerate_rectangular'];a=x['payoffs'];v=F(x['value'])
        for p in x['row']['optimal_vertices']:
            for q in x['column_negative_game']['optimal_vertices']:
                rows,cols,pay=direct(a,p['strategy'],q['strategy']);self.assertEqual(pay,v);self.assertTrue(all(s<=v for s in rows));self.assertTrue(all(s>=v for s in cols))
        c=x['certificate'];self.assertEqual(c['row_complementarity_products'],['0']*4);self.assertEqual(c['column_complementarity_products'],['0']*2)
    def test_coordinate_ranges_have_attaining_vertices(self):
        for a in ([[2]*4]*4,[[1,-1],[1,-1],[-1,1],[-2,-2]],[[3,0],[1,2]]):
            x=solve(a)
            for key in ('row','column_negative_game'):
                s=x[key]
                for r in s['coordinate_ranges']:
                    vals=[F(v['strategy'][r['coordinate']]) for v in s['optimal_vertices']]
                    self.assertEqual(F(r['minimum']),min(vals));self.assertEqual(F(r['maximum']),max(vals));self.assertEqual(vals[r['minimum_vertex']],min(vals));self.assertEqual(vals[r['maximum_vertex']],max(vals))
    def test_convex_optimal_mixtures_remain_equilibria(self):
        a=[[1,-1],[1,-1],[-1,1],[-2,-2]]
        for k in range(11):
            t=F(k,10);p=[t/2,(1-t)/2,F(1,2),0];self.assertTrue(audit(a,p,[F(1,2)]*2)['is_equilibrium'])
    def test_audit_all_grid_strategies(self):
        a=[[3,0],[1,2]];v=F(3,2)
        for i,j in product(range(9),repeat=2):
            p=[F(i,8),1-F(i,8)];q=[F(j,8),1-F(j,8)];x=audit(a,p,q);rows,cols,pay=direct(a,p,q)
            self.assertEqual(F(x['payoff']),pay);self.assertEqual(F(x['row_deviation_gain']),max(rows)-pay);self.assertEqual(F(x['column_deviation_gain']),pay-min(cols));self.assertEqual(F(x['row_exploitability']),v-min(cols));self.assertEqual(F(x['column_exploitability']),max(rows)-v);self.assertEqual(F(x['duality_gap']),max(rows)-min(cols))
    def test_best_reply_ties_and_pure_failure(self):
        x=demo()['pure_policy_failure'];self.assertEqual(x['row_best_replies'],[1]);self.assertEqual(x['column_best_replies'],[1]);self.assertEqual(x['duality_gap'],'2')
        x=audit([[2,2],[2,2]],['1/3','2/3'],['2/3','1/3']);self.assertEqual(x['row_best_replies'],[0,1]);self.assertEqual(x['column_best_replies'],[0,1]);self.assertTrue(x['is_equilibrium'])
    def test_positive_affine_payoff_transform(self):
        a=[[1,-1],[1,-1],[-1,1],[-2,-2]];x=solve(a);y=solve([[F(7,3)*v-F(5,2) for v in row] for row in a])
        self.assertEqual(F(y['value']),F(7,3)*F(x['value'])-F(5,2))
        for k in ('row','column_negative_game'):self.assertEqual([v['strategy'] for v in x[k]['optimal_vertices']],[v['strategy'] for v in y[k]['optimal_vertices']])
    def test_negative_transpose_swaps_players(self):
        a=[[1,-1],[1,-1],[-1,1],[-2,-2]];x=solve(a);y=solve([[-a[i][j] for i in range(4)] for j in range(2)])
        self.assertEqual(F(y['value']),-F(x['value']));self.assertEqual(y['row']['representative'],x['column_negative_game']['representative']);self.assertEqual(y['column_negative_game']['representative'],x['row']['representative'])
    def test_row_column_permutation(self):
        a=[[3,0,5],[1,2,-1],[4,-2,1]];x=solve(a);rp=[2,0,1];cp=[1,2,0];y=solve([[a[i][j] for j in cp] for i in rp]);self.assertEqual(y['value'],x['value']);self.assertEqual(y['row']['representative'],[x['row']['representative'][i] for i in rp]);self.assertEqual(y['column_negative_game']['representative'],[x['column_negative_game']['representative'][i] for i in cp])
    def test_perturbation_strategy_discontinuity(self):
        x=demo()['perturbation_flip'];self.assertEqual(x['epsilon'],'1/1000000000000');self.assertEqual(x['value_change'],'0');self.assertEqual(x['original']['row']['representative'],['0','1']);self.assertEqual(x['changed']['row']['representative'],['1','0']);self.assertEqual(x['old_pair_in_changed_game']['duality_gap'],x['epsilon'])
    def test_perturbation_value_bound_attained(self):
        a=[[1,-1],[-1,1]];x=perturbation(a,[[F(v)+F(1,7) for v in row] for row in a]);self.assertEqual(x['value_change'],'1/7');self.assertEqual(x['value_shift_slack'],'0');self.assertEqual(x['old_pair_in_changed_game']['duality_gap'],'0')
    def test_pair_transfer_bound_approached(self):
        d=F(1,1000);x=perturbation([[0,d],[-d,0]],[[0,d-1],[1-d,0]])
        self.assertEqual(x['original']['row']['representative'],['1','0']);self.assertEqual(x['original']['column_negative_game']['representative'],['1','0'])
        self.assertEqual(F(x['old_pair_in_changed_game']['duality_gap']),2-2*d);self.assertEqual(x['epsilon'],'1');self.assertEqual(F(x['pair_transfer_slack']),2*d)
    def test_perturbation_all_small_two_by_two(self):
        a=[[1,-1],[-1,1]]
        for delta in product((F(-1,3),F(1,3)),repeat=4):
            b=[[F(a[i][j])+delta[2*i+j] for j in range(2)] for i in range(2)];x=perturbation(a,b);eps=F(x['epsilon'])
            self.assertLessEqual(abs(F(x['value_change'])),eps);self.assertLessEqual(F(x['old_pair_in_changed_game']['duality_gap']),2*eps);self.assertTrue(all(F(x[k])>=0 for k in ('row_transfer_slack','column_transfer_slack','pair_transfer_slack','value_shift_slack')))
    def test_zero_perturbation(self):
        a=[[3,0],[1,2]];x=perturbation(a,a);self.assertEqual(x['epsilon'],'0');self.assertEqual(x['pair_transfer_slack'],'0');self.assertEqual(x['original'],x['changed'])
    def test_full_four_by_four_capacity(self):
        a=[[0,-1,1,2],[1,0,-1,2],[-1,1,0,2],[-2,-2,-2,-2]];x=solve(a)
        self.assertEqual(x['row']['basis_budget'],70);self.assertEqual(x['column_negative_game']['basis_budget'],70);self.assertEqual(x['value'],'0');self.assertEqual(x['row']['representative'],['1/3','1/3','1/3','0']);self.assertEqual(x['column_negative_game']['representative'],['1/3','1/3','1/3','0'])
    def test_no_mutation_or_global_rng(self):
        a=[[1,-1],[-1,1]];p=['1/3','2/3'];q=['1/2','1/2'];saved=copy.deepcopy((a,p,q));state=random.getstate();solve(a);audit(a,p,q);perturbation(a,a);self.assertEqual((a,p,q),saved);self.assertEqual(random.getstate(),state)
    def test_exact_parsing(self):
        for v in ('1.25','-3/7',3,F(2,5)):self.assertEqual(rational(v),F(v))
        self.assertEqual(solve([['1.25']])['value'],'5/4')
    def test_input_number_rejections(self):
        for v in (True,0.5,'nan','1e3','1/0',' '*2+'1',str(1<<513),'1'*161,None):
            with self.assertRaises(ValueError):solve([[v]])
    def test_matrix_shape_rejections(self):
        for a in ([],[[]],[[1],[1,2]],[[1]]*5,[[1]*5],None,'x',[1]):
            with self.assertRaises(ValueError):solve(a)
        with self.assertRaises(ValueError):perturbation([[1]],[[1,2]])
    def test_strategy_rejections(self):
        for p in ([],[1],[1,1],[-1,2],[True,0],[0.5,0.5],None):
            with self.assertRaises(ValueError):audit([[1,-1],[-1,1]],p,['1/2','1/2'])
        with self.assertRaises(ValueError):audit([[1,-1],[-1,1]],['1/2','1/2'],[2,-1])
    def test_exact_elimination_reference(self):
        a=[[2,3,1],[4,1,-3],[1,2,2]];b=[1,-1,3];x=elimination(a,b);self.assertEqual(x['determinant'],determinant(a));self.assertEqual(x['rank'],3)
        for row,v in zip(a,b):self.assertEqual(sum(F(q)*w for q,w in zip(row,x['solution'])),v)
        self.assertIsNone(elimination([[1,1],[2,2]],[1,2])['solution'])
    def test_all_cli_fixture_modes(self):
        for mode in ('demo','solve','audit','perturbation'):
            args=[] if mode=='demo' else [str(ROOT/'examples'/f'{mode}-input.json')];p=subprocess.run([sys.executable,'-m','gamelab',mode]+args,cwd=ROOT,capture_output=True,text=True)
            self.assertEqual(p.returncode,0,p.stderr);self.assertEqual(p.stderr,'');json.loads(p.stdout)
            if mode=='demo':self.assertEqual(p.stdout,(ROOT/'examples/demo.json').read_text())
    def test_cli_schema_and_number_errors(self):
        cases=['{}','[]','{"schema_version":true,"payoffs":[[1]]}','{"schema_version":1,"payoffs":[[0.5]]}','{"schema_version":1,"payoffs":[[NaN]]}','{"schema_version":1,"payoffs":[[1]],"unknown":1}','{"schema_version":1,"schema_version":1,"payoffs":[[1]]}']
        with tempfile.TemporaryDirectory() as d:
            path=Path(d)/'x.json'
            for s in cases:
                path.write_text(s);p=subprocess.run([sys.executable,'-m','gamelab','solve',str(path)],cwd=ROOT,capture_output=True,text=True);self.assertEqual(p.returncode,2);self.assertEqual(p.stdout,'');self.assertTrue(p.stderr.startswith('error:'))
            for raw in (b'\xff',b' '*200001):
                path.write_bytes(raw);p=subprocess.run([sys.executable,'-m','gamelab','solve',str(path)],cwd=ROOT,capture_output=True,text=True);self.assertEqual(p.returncode,2);self.assertEqual(p.stdout,'')
    def test_cli_usage_and_missing_file(self):
        for args in ([],['foo'],['solve','/no/such/file'],['audit',str(ROOT/'examples/solve-input.json')]):
            p=subprocess.run([sys.executable,'-m','gamelab']+args,cwd=ROOT,capture_output=True,text=True);self.assertEqual(p.returncode,2);self.assertEqual(p.stdout,'')
