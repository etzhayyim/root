from typing import TypedDict, Annotated, List
from langgraph.graph import StateGraph, END

class MineralProcurementState(TypedDict):
    commodity_code: str
    compliance_status: bool
    validation_steps: List[str]
    logistics_ready: bool

def validate_purity(state: MineralProcurementState) -> MineralProcurementState:
    state['validation_steps'].append('purity_verified')
    state['compliance_status'] = True
    return state

def check_logistics(state: MineralProcurementState) -> MineralProcurementState:
    state['validation_steps'].append('logistics_cleared')
    state['logistics_ready'] = True
    return state

graph = StateGraph(MineralProcurementState)
graph.add_node('validate', validate_purity)
graph.add_node('logistics', check_logistics)
graph.add_edge('validate', 'logistics')
graph.add_edge('logistics', END)
graph.set_entry_point('validate')
graph = graph.compile()
