from langgraph.graph import StateGraph, END
from typing import TypedDict, List

class UrologicalState(TypedDict):
    item_id: str
    is_sterile: bool
    compliance_docs: List[str]
    approved: bool

def validate_sterilization(state: UrologicalState):
    state['is_sterile'] = True
    return state

def check_regulatory_compliance(state: UrologicalState):
    state['approved'] = len(state['compliance_docs']) > 0
    return state

graph = StateGraph(UrologicalState)
graph.add_node('sterility_check', validate_sterilization)
graph.add_node('regulatory_check', check_regulatory_compliance)
graph.set_entry_point('sterility_check')
graph.add_edge('sterility_check', 'regulatory_check')
graph.add_edge('regulatory_check', END)
app = graph.compile()
