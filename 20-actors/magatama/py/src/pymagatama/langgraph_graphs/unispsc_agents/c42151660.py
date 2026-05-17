from typing import TypedDict, List
from langgraph.graph import StateGraph, END

class DentalState(TypedDict):
    material_type: str
    is_sterile: bool
    absorption_rate: float
    compliance_docs: List[str]
    approved: bool

def validate_compliance(state: DentalState):
    state['approved'] = state['is_sterile'] and len(state['compliance_docs']) > 0
    return state

def process_spec(state: DentalState):
    print(f'Processing material: {state['material_type']}')
    return state

graph = StateGraph(DentalState)
graph.add_node('validate', validate_compliance)
graph.add_node('process', process_spec)
graph.set_entry_point('validate')
graph.add_edge('validate', 'process')
graph.add_edge('process', END)
graph = graph.compile()