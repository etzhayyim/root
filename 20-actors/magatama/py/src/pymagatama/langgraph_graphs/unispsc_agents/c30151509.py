from typing import TypedDict, List
from langgraph.graph import StateGraph, END

class TrussState(TypedDict):
    spec_data: dict
    validation_passed: bool
    errors: List[str]

def validate_load_specs(state: TrussState):
    load = state['spec_data'].get('load_capacity')
    if not load or load <= 0:
        return {'validation_passed': False, 'errors': ['Invalid load capacity']}
    return {'validation_passed': True}

def structural_compliance(state: TrussState):
    if 'CAD_verified' not in state['spec_data']:
        return {'validation_passed': False, 'errors': ['CAD drawing missing verification']}
    return {'validation_passed': True}

graph = StateGraph(TrussState)
graph.add_node('load_check', validate_load_specs)
graph.add_node('cad_check', structural_compliance)
graph.set_entry_point('load_check')
graph.add_edge('load_check', 'cad_check')
graph.add_edge('cad_check', END)
graph = graph.compile()
