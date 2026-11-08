import base64
import copy
from fractions import Fraction as F
import importlib.util
import json
from pathlib import Path
import unittest
import xml.etree.ElementTree as ET
import zlib
from gamelab import interval_demo
ROOT=Path(__file__).resolve().parents[1]
spec=importlib.util.spec_from_file_location('render_intervals',ROOT/'examples/render_intervals.py');module=importlib.util.module_from_spec(spec);spec.loader.exec_module(module)
NS={'s':'http://www.w3.org/2000/svg'}
class IntervalFigureTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):cls.r=interval_demo();cls.text=module.render(cls.r);cls.root=ET.fromstring(cls.text)
    def test_all_29_cells(self):
        e={};s=self.r['shared_entry_conflict'];c=s['chosen_pair']
        for key in ('lower','upper'):
            for i,row in enumerate(s[key]):
                for j,v in enumerate(row):e[f'{key}-{i}-{j}']=v
        e.update({'shared-gap':c['worst_gap'],'separate':c['sum_separately_maximized_deviations'],'value-width':s['value_range']['width'],'robust-gap':s['robust_security_pair']['exact_box_audit']['worst_gap']})
        for k in range(3):
            # Independent direct pure-policy formula: row=max(t,1)-t, column=t-min(t,1).
            vals={'entry':k,'row':max(k,1)-k,'column':k-min(k,1),'gap':abs(k-1)}
            for key,v in vals.items():e[f'probe-{k}-{key}']=str(v)
        f=self.r['full_box'];one=self.r['singleton_cancellation'];e.update({'full-gap':f['chosen_pair']['worst_gap'],'full-separate':f['chosen_pair']['sum_separately_maximized_deviations'],'full-width':f['value_range']['width'],'singleton-width':one['value_range']['width'],'singleton-gap':one['chosen_pair']['worst_gap']})
        self.assertEqual(len(e),29);self.assertEqual(len(self.root.findall("s:text[@data-value]",NS)),29)
        for key,value in e.items():
            cell=self.root.find(f"s:text[@id='cell-{key}']",NS);self.assertEqual(cell.text,str(value));self.assertEqual(cell.attrib['data-value'],str(value));self.assertTrue(20<float(cell.attrib['x'])<1070);self.assertTrue(20<float(cell.attrib['y'])<1060)
    def test_complete_metadata_and_hidden_support_tamper(self):
        blob=self.root.find("s:metadata[@id='report-zlib-base64']",NS).text;self.assertEqual(json.loads(zlib.decompress(base64.b64decode(blob))),self.r)
        x=copy.deepcopy(self.r);x['full_box']['chosen_pair']['reply_pairs'][0]['coefficients'][1][1]='99/7';self.assertNotEqual(module.render(x),self.text)
    def test_byte_exact(self):self.assertEqual((ROOT/'assets/interval-audit.svg').read_text(),self.text)
