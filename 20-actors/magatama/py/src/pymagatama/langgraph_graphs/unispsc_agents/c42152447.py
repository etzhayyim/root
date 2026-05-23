from typing import TypedDict, Annotated
from langgraph.graph import StateGraph, END

class DentalSupplyState(TypedDict):
    item_id: str
    compliance_docs: list
    is_approved: bool

def validate_compliance(state: DentalSupplyState):
    # Verify SDS and ISO certificates for dental supplies
    has_sds = 'SDS' in state['compliance_docs']
    has_iso = 'ISO-13485' in state['compliance_docs']
    return {'is_approved': has_sds and has_iso}

graph = StateGraph(DentalSupplyState)
graph.add_node('validate', validate_compliance)
graph.set_entry_point('validate')
graph.add_edge('validate', END)
graph = graph.compile()
