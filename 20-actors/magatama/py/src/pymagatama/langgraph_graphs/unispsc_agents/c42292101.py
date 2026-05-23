from typing import TypedDict, List
from langgraph.graph import StateGraph, END

class SurgicalProcurementState(TypedDict):
    part_number: str
    is_sterile: bool
    compliance_docs: List[str]
    approved: bool

def validate_certification(state: SurgicalProcurementState):
    state['approved'] = 'ISO13485' in state['compliance_docs'] and state['is_sterile']
    return state

graph = StateGraph(SurgicalProcurementState)
graph.add_node('validate', validate_certification)
graph.set_entry_point('validate')
graph.add_edge('validate', END)
graph = graph.compile()
