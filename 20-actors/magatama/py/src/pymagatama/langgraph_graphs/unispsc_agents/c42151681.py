from typing import TypedDict, List
from langgraph.graph import StateGraph, END

class DentalSupplyState(TypedDict):
    item_name: str
    compliance_docs: List[str]
    is_sterile: bool
    approved: bool

def validate_compliance(state: DentalSupplyState):
    required = ['FDA_Approval', 'ISO_13485']
    state['approved'] = all(doc in state['compliance_docs'] for doc in required)
    return state

def check_sterility(state: DentalSupplyState):
    state['is_sterile'] = True
    return state

graph = StateGraph(DentalSupplyState)
graph.add_node('validate', validate_compliance)
graph.add_node('check_sterility', check_sterility)
graph.add_edge('validate', 'check_sterility')
graph.add_edge('check_sterility', END)
graph.set_entry_point('validate')
app = graph.compile()
