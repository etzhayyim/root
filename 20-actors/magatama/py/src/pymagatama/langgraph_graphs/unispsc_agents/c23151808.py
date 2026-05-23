from typing import TypedDict
from langgraph.graph import StateGraph, END

class LaserWelderState(TypedDict):
    specs: dict
    validated: bool
    compliance_check: bool

def validate_specs(state: LaserWelderState):
    state['validated'] = state['specs'].get('power', 0) > 0
    return state

def check_compliance(state: LaserWelderState):
    state['compliance_check'] = state.get('validated', False)
    return state

graph = StateGraph(LaserWelderState)
graph.add_node('validate', validate_specs)
graph.add_node('compliance', check_compliance)
graph.set_entry_point('validate')
graph.add_edge('validate', 'compliance')
graph.add_edge('compliance', END)
graph = graph.compile()
