from typing import TypedDict
from langgraph.graph import StateGraph, END
class EndoscopyProcurementState(TypedDict):
    instrument_id: str
    compliance_docs: list
    sterile_check: bool
    approved: bool
def validate_compliance(state: EndoscopyProcurementState):
    state['approved'] = len(state['compliance_docs']) >= 3 and state['sterile_check']
    return state
graph = StateGraph(EndoscopyProcurementState)
graph.add_node('validate', validate_compliance)
graph.set_entry_point('validate')
graph.add_edge('validate', END)
