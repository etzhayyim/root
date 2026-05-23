from typing import TypedDict, List
from langgraph.graph import StateGraph, END

class ChemicalProcurementState(TypedDict):
    commodity_code: str
    purity_level: float
    compliance_docs: List[str]
    is_approved: bool

def validate_purity(state: ChemicalProcurementState) -> ChemicalProcurementState:
    if state['purity_level'] >= 99.5:
        state['is_approved'] = True
    else:
        state['is_approved'] = False
    return state

def check_msds(state: ChemicalProcurementState) -> ChemicalProcurementState:
    if 'MSDS' in state['compliance_docs']:
        state['is_approved'] = state['is_approved'] and True
    else:
        state['is_approved'] = False
    return state

graph = StateGraph(ChemicalProcurementState)
graph.add_node('validate_purity', validate_purity)
graph.add_node('check_msds', check_msds)
graph.add_edge('validate_purity', 'check_msds')
graph.add_edge('check_msds', END)
graph.set_entry_point('validate_purity')
graph = graph.compile()
