from typing import TypedDict, List
from langgraph.graph import StateGraph, END

class ClothingState(TypedDict):
    item_id: str
    safety_certs: List[str]
    compliance_status: bool

def validate_safety_protocols(state: ClothingState):
    required = ['EN71', 'FLAME_RETARDANT', 'NON_TOXIC_DYE']
    state['compliance_status'] = all(c in state['safety_certs'] for c in required)
    return state

def check_compliance(state: ClothingState):
    return 'compliant' if state['compliance_status'] else 'flagged'

graph = StateGraph(ClothingState)
graph.add_node('safety_check', validate_safety_protocols)
graph.add_edge('safety_check', END)
graph.set_entry_point('safety_check')
graph = graph.compile()
