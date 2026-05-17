from typing import TypedDict, Annotated, Sequence
import operator
from langgraph.graph import StateGraph, END

class MineralProcurementState(TypedDict):
    commodity_code: str
    purity_level: float
    compliance_docs: Annotated[Sequence[str], operator.add]
    is_cleared: bool

def validate_purity(state: MineralProcurementState) -> MineralProcurementState:
    state['is_cleared'] = state['purity_level'] >= 99.9
    return state

def check_compliance(state: MineralProcurementState) -> MineralProcurementState:
    if 'MSDS' in state['compliance_docs'] and 'EXPORT_CERT' in state['compliance_docs']:
        state['is_cleared'] = state['is_cleared'] and True
    else:
        state['is_cleared'] = False
    return state

graph = StateGraph(MineralProcurementState)
graph.add_node('validate_purity', validate_purity)
graph.add_node('check_compliance', check_compliance)
graph.set_entry_point('validate_purity')
graph.add_edge('validate_purity', 'check_compliance')
graph.add_edge('check_compliance', END)
graph = graph.compile()