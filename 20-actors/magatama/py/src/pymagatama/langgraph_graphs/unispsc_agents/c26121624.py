from langgraph.graph import StateGraph, END
from typing import TypedDict, List

class CableState(TypedDict):
    specs: dict
    validation_passed: bool
    log: List[str]

def validate_specs(state: CableState):
    required = ['pitch_spacing', 'number_of_conductors']
    passed = all(field in state['specs'] for field in required)
    return {'validation_passed': passed, 'log': ['Spec validation checked']}

def check_compliance(state: CableState):
    is_compliant = state['specs'].get('rohs_compliance', False)
    return {'log': [f'Compliance status: {is_compliant}']}

graph = StateGraph(CableState)
graph.add_node('validate', validate_specs)
graph.add_node('compliance', check_compliance)
graph.set_entry_point('validate')
graph.add_edge('validate', 'compliance')
graph.add_edge('compliance', END)
graph = graph.compile()