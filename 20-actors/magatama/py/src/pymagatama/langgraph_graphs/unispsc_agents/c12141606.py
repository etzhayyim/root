from typing import TypedDict, Annotated, List
from langgraph.graph import StateGraph, END
from langgraph.graph.message import add_messages

class ChemicalProcurementState(TypedDict):
    commodity_id: str
    purity_level: float
    compliance_checks: List[str]
    validation_status: str

def validate_purity(state: ChemicalProcurementState) -> ChemicalProcurementState:
    if state['purity_level'] < 99.9:
        state['validation_status'] = 'REJECTED_LOW_PURITY'
    else:
        state['validation_status'] = 'PURITY_VERIFIED'
    return state

def check_compliance(state: ChemicalProcurementState) -> ChemicalProcurementState:
    if 'REJECTED' in state['validation_status']:
        return state
    state['compliance_checks'] = ['SDS_VERIFIED', 'EXPORT_CONTROL_CLEARED']
    state['validation_status'] = 'READY_FOR_PURCHASE'
    return state

graph = StateGraph(ChemicalProcurementState)
graph.add_node('validate_purity', validate_purity)
graph.add_node('check_compliance', check_compliance)
graph.set_entry_point('validate_purity')
graph.add_edge('validate_purity', 'check_compliance')
graph.add_edge('check_compliance', END)
app = graph.compile()
