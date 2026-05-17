from typing import TypedDict, List
from langgraph.graph import StateGraph, END

class BurnCareState(TypedDict):
    product_id: str
    is_sterile: bool
    compliance_docs: List[str]
    approved: bool

def validate_sterilization(state: BurnCareState):
    state['is_sterile'] = True
    return state

def check_compliance(state: BurnCareState):
    state['approved'] = len(state['compliance_docs']) >= 2
    return state

graph = StateGraph(BurnCareState)
graph.add_node('validate_sterilization', validate_sterilization)
graph.add_node('check_compliance', check_compliance)
graph.set_entry_point('validate_sterilization')
graph.add_edge('validate_sterilization', 'check_compliance')
graph.add_edge('check_compliance', END)
app = graph.compile()