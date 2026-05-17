from typing import TypedDict
from langgraph.graph import StateGraph, END

class PumpState(TypedDict):
    spec_data: dict
    validated: bool
    compliance_check: bool

def validate_specs(state: PumpState):
    temp = state['spec_data'].get('temp', 0)
    state['validated'] = temp <= -150
    return state

def compliance_workflow(state: PumpState):
    state['compliance_check'] = state['validated']
    return state

graph = StateGraph(PumpState)
graph.add_node('validate', validate_specs)
graph.add_node('compliance', compliance_workflow)
graph.set_entry_point('validate')
graph.add_edge('validate', 'compliance')
graph.add_edge('compliance', END)
graph = graph.compile()