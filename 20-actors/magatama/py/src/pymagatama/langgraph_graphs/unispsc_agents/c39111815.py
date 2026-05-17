from typing import TypedDict, List
from langgraph.graph import StateGraph, END

class GuardState(TypedDict):
    material: str
    spec_check: bool
    approved: bool

def validate_material(state: GuardState):
    state['spec_check'] = state['material'] in ['Steel', 'Stainless Steel', 'Aluminum']
    return 'validate_material'

def check_compliance(state: GuardState):
    state['approved'] = state['spec_check']
    return 'check_compliance'

graph = StateGraph(GuardState)
graph.add_node('validate', validate_material)
graph.add_node('compliance', check_compliance)
graph.add_edge('validate', 'compliance')
graph.add_edge('compliance', END)
graph.set_entry_point('validate')
graph = graph.compile()