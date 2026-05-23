from langgraph.graph import StateGraph, END
from typing import TypedDict

class TubeState(TypedDict):
    tube_id: str
    is_sterile: bool
    compliance_docs: list
    status: str

def check_compliance(state: TubeState):
    # Business logic for medical device compliance checking
    state['status'] = 'COMPLIANT' if state['is_sterile'] else 'FAILED'
    return state

graph = StateGraph(TubeState)
graph.add_node('verify', check_compliance)
graph.set_entry_point('verify')
graph.add_edge('verify', END)
graph = graph.compile()
