from typing import TypedDict, List
from langgraph.graph import StateGraph, END

class AssemblyState(TypedDict):
    part_specs: dict
    validation_results: List[str]
    is_compliant: bool

def validate_material(state: AssemblyState):
    specs = state['part_specs']
    valid = 'ASTM_B' in specs.get('standards', [])
    return {'validation_results': ['Material compliance check passed'] if valid else ['Material mismatch'], 'is_compliant': valid}

def validate_joint(state: AssemblyState):
    if state['is_compliant']:
        return {'validation_results': state['validation_results'] + ['Joint pressure test passed']}
    return state

graph = StateGraph(AssemblyState)
graph.add_node('material_check', validate_material)
graph.add_node('joint_audit', validate_joint)
graph.set_entry_point('material_check')
graph.add_edge('material_check', 'joint_audit')
graph.add_edge('joint_audit', END)
graph = graph.compile()