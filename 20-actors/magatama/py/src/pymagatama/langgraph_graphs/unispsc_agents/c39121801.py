from typing import TypedDict
from langgraph.graph import StateGraph, END

class ControlUnitState(TypedDict):
    spec: dict
    validated: bool
    error: str

def validate_specs(state: ControlUnitState):
    required = ['voltage', 'protocol', 'ip_rating']
    valid = all(k in state['spec'] for k in required)
    return {'validated': valid, 'error': '' if valid else 'Missing specs'}

def check_compliance(state: ControlUnitState):
    if state['validated']:
        return {'validated': True}
    return {'validated': False, 'error': 'Compliance check failed'}

graph = StateGraph(ControlUnitState)
graph.add_node('validate', validate_specs)
graph.add_node('compliance', check_compliance)
graph.set_entry_point('validate')
graph.add_edge('validate', 'compliance')
graph.add_edge('compliance', END)
graph = graph.compile()
