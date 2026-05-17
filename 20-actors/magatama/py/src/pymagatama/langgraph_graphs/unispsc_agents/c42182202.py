from typing import TypedDict
from langgraph.graph import StateGraph, END

class ThermometerState(TypedDict):
    spec_data: dict
    validated: bool
    error: str

def validate_specs(state: ThermometerState):
    required = ['accuracy', 'calibration_date', 'iso_cert']
    missing = [f for f in required if f not in state['spec_data']]
    return {'validated': len(missing) == 0, 'error': f'Missing: {missing}' if missing else ''}

def check_compliance(state: ThermometerState):
    if not state.get('validated'): return {'validated': False}
    return {'validated': True}

graph = StateGraph(ThermometerState)
graph.add_node('validate', validate_specs)
graph.add_node('compliance', check_compliance)
graph.set_entry_point('validate')
graph.add_edge('validate', 'compliance')
graph.add_edge('compliance', END)
graph = graph.compile()