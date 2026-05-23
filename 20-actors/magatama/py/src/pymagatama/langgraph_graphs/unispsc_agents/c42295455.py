from typing import TypedDict
from langgraph.graph import StateGraph, END

class CranialKitState(TypedDict):
    iso_cert: bool
    sterilization_valid: bool
    approval_status: str

def validate_certification(state: CranialKitState):
    state['approval_status'] = 'APPROVED' if state['iso_cert'] and state['sterilization_valid'] else 'REJECTED'
    return state

graph = StateGraph(CranialKitState)
graph.add_node('validate', validate_certification)
graph.set_entry_point('validate')
graph.add_edge('validate', END)
app = graph.compile()
