from typing import TypedDict
from langgraph.graph import StateGraph, END

class GatlingProcessState(TypedDict):
    caliber: float
    compliance_cleared: bool
    test_fired: bool

def validate_specs(state: GatlingProcessState):
    state['compliance_cleared'] = (state['caliber'] > 0)
    return state

def run_security_check(state: GatlingProcessState):
    return {'test_fired': True}

graph = StateGraph(GatlingProcessState)
graph.add_node('validate', validate_specs)
graph.add_node('security', run_security_check)
graph.set_entry_point('validate')
graph.add_edge('validate', 'security')
graph.add_edge('security', END)
graph = graph.compile()
