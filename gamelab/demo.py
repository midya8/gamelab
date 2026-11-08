"""Developed controls, not observed multi-agent outcomes."""
from .core import solve,audit,perturbation


def demo():
    rps=[[0,-1,1],[1,0,-1],[-1,1,0]]
    duplicated=[[1,-1],[1,-1],[-1,1],[-2,-2]]
    # Unique preferred action flips under an arbitrarily small signed perturbation.
    tiny='1/1000000000000'
    flip=perturbation([[0],[tiny]],[[tiny],[0]])
    out={'schema_version':1,'matching_pennies':solve([[1,-1],[-1,1]]),
         'cyclic':solve(rps),'pure_policy_failure':audit(rps,[1,0,0],[1,0,0]),
         'degenerate_rectangular':solve(duplicated),
         'mixed_degenerate_pair':audit(duplicated,['1/8','3/8','1/2',0],['1/2','1/2']),
         'constant_game':solve([[2,2,2],[2,2,2]]),
         'nonzero_value':solve([[3,0],[1,2]]),
         'perturbation_flip':flip,
         'scope':'developed exact matrices; no trained agent tournament or empirical generalization guarantee'}
    assert out['matching_pennies']['value']=='0'
    assert len(out['degenerate_rectangular']['row']['optimal_vertices'])==2
    assert not out['degenerate_rectangular']['row']['unique_optimal_strategy']
    assert out['degenerate_rectangular']['row']['coordinate_ranges'][3]['maximum']=='0'
    assert out['mixed_degenerate_pair']['is_equilibrium']
    assert out['pure_policy_failure']['duality_gap']=='2'
    assert out['nonzero_value']['value']=='3/2'
    assert flip['old_pair_in_changed_game']['duality_gap']==tiny
    return out
