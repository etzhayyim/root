from langgraph.graph import StateGraph, END
from typing import TypedDict, List

class DentalPartState(TypedDict):
    part_id: str
    compliance_docs: List[str]
    approved: bool

def validate_compliance(state: DentalPartState):
    required = ['ISO13485', 'RegulatoryClearance']
    all_present = all(doc in state['compliance_docs'] for doc in required)
    return {'approved': all_present}

def route_by_approval(state: DentalPartState):
    return 'approved' if state['approved'] else END

graph = StateGraph(DentalPartState)
graph.add_node('validate', validate_compliance)
graph.set_entry_point('validate')
graph.add_edge('validate', END)
graph.compile()