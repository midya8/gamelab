import base64
import copy
from fractions import Fraction as F
import importlib.util
import json
from pathlib import Path
import unittest
import xml.etree.ElementTree as ET
import zlib
from gamelab import demo
ROOT=Path(__file__).resolve().parents[1]
spec=importlib.util.spec_from_file_location('render_demo',ROOT/'examples/render_demo.py');module=importlib.util.module_from_spec(spec);spec.loader.exec_module(module)
NS={'s':'http://www.w3.org/2000/svg'}
class FigureTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):cls.r=demo();cls.text=module.render(cls.r);cls.root=ET.fromstring(cls.text)
    def test_all_23_cells(self):
        expected={}
        for i,row in enumerate(self.r['cyclic']['payoffs']):
            for j,v in enumerate(row):expected[f'matrix-{i}-{j}']=v
        expected.update(value=self.r['cyclic']['value'],row_maximin=self.r['cyclic']['pure_strategy_controls']['row_maximin'],column_minimax=self.r['cyclic']['pure_strategy_controls']['column_minimax'])
        for k,v in enumerate(self.r['degenerate_rectangular']['row']['optimal_vertices']):
            for i,p in enumerate(v['strategy']):expected[f'vertex-{k}-{i}']=p
        f=self.r['perturbation_flip'];expected.update(epsilon=f['epsilon'],**{'value-change':f['value_change'],'transfer-gap':f['old_pair_in_changed_game']['duality_gap']})
        self.assertEqual(len(expected),23)
        for k,v in expected.items():
            e=self.root.find(f"s:text[@id='cell-{k}']",NS);self.assertEqual(e.text,str(v));self.assertEqual(e.attrib['data-value'],str(v));self.assertTrue(20<float(e.attrib['x'])<1070);self.assertTrue(20<float(e.attrib['y'])<1180)
    def test_all_four_ranges_and_eight_endpoints(self):
        for i,r in enumerate(self.r['degenerate_rectangular']['row']['coordinate_ranges']):
            e=self.root.find(f"s:line[@id='range-{i}']",NS)
            self.assertEqual(F(e.attrib['data-min']),F(r['minimum']));self.assertEqual(F(e.attrib['data-max']),F(r['maximum']))
            for side,field in (('minimum','x1'),('maximum','x2')):
                x=180+350*float(F(r[side]));self.assertAlmostEqual(float(e.attrib[field]),x,delta=.00051)
                circle=self.root.find(f"s:circle[@id='range-{i}-{side}']",NS);self.assertAlmostEqual(float(circle.attrib['cx']),x,delta=.00051);self.assertEqual(float(circle.attrib['cy']),527+47*i)
    def test_complete_metadata_and_hidden_basis_tamper(self):
        blob=self.root.find("s:metadata[@id='report-zlib-base64']",NS).text;self.assertEqual(json.loads(zlib.decompress(base64.b64decode(blob))),self.r)
        x=copy.deepcopy(self.r);x['constant_game']['row']['attempts'][0]['determinant']='99/7';self.assertNotEqual(module.render(x),self.text)
    def test_byte_exact(self):self.assertEqual((ROOT/'assets/minimax-audit.svg').read_text(),self.text)
