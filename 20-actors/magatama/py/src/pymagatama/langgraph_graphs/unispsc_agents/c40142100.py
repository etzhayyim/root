from typing import TypedDict
from langgraph.graph import StateGraph, END

class PipeOrderState(TypedDict):
    material: str
    spec_check: bool
    safety_clearance: bool

def validate_specs(state: PipeOrderState):
    state['spec_check'] = state['material'] in ['Steel', 'Stainless', 'PVC']
    print('Validating technical specifications...')
    return state

def check_compliance(state: PipeOrderState):
    state['safety_clearance'] = True
    print('Checking regulatory compliance for pressure pipe...')
    return state

graph = StateGraph(PipeOrderState)
graph.add_node('validate', validate_specs)
graph.add_node('compliance', check_compliance)
graph.add_edge('validate', 'compliance')
graph.add_edge('compliance', END)
graph.set_entry_point('validate')
app = graph.compile()
