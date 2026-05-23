from langgraph.graph import StateGraph, END
from typing import TypedDict, List

class RehabState(TypedDict):
    equipment_id: str
    safety_check: bool
    compliance_docs: List[str]
    approved: bool

def validate_specs(state: RehabState):
    # Simulate geometric integrity check for physical therapy lift accessories
    state['safety_check'] = True if state.get('equipment_id') else False
    return state

def check_compliance(state: RehabState):
    # Verify ISO 13485 certification documents
    state['approved'] = 'ISO13485' in state['compliance_docs']
    return state

graph = StateGraph(RehabState)
graph.add_node('validate', validate_specs)
graph.add_node('compliance', check_compliance)
graph.add_edge('validate', 'compliance')
graph.add_edge('compliance', END)
graph.set_entry_point('validate')
graph = graph.compile()
