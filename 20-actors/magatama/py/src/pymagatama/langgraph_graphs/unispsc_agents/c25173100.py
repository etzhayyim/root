from typing import TypedDict
from langgraph.graph import StateGraph, END

class NavComponentState(TypedDict):
    specs: dict
    validation_status: str
    compliance_risk: bool

def validate_specs(state: NavComponentState):
    required = ['Accuracy_Meters', 'Encryption_Standard']
    state['validation_status'] = 'pass' if all(k in state['specs'] for k in required) else 'fail'
    return state

def check_export_control(state: NavComponentState):
    state['compliance_risk'] = state['specs'].get('precision', 0) < 0.1
    return state

graph = StateGraph(NavComponentState)
graph.add_node('validate', validate_specs)
graph.add_node('compliance', check_export_control)
graph.add_edge('validate', 'compliance')
graph.add_edge('compliance', END)
graph.set_entry_point('validate')
graph = graph.compile()