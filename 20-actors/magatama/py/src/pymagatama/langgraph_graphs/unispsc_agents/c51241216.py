from typing import TypedDict
from langgraph.graph import StateGraph, END

class ChemicalProcurementState(TypedDict):
    purity_level: float
    has_sds: bool
    is_compliant: bool

def validate_purity(state: ChemicalProcurementState):
    state['is_compliant'] = state['purity_level'] >= 98.0
    return state

def check_documentation(state: ChemicalProcurementState):
    if not state['has_sds']:
        raise ValueError('Missing mandatory SDS document')
    return state

graph = StateGraph(ChemicalProcurementState)
graph.add_node('validate_purity', validate_purity)
graph.add_node('check_documentation', check_documentation)
graph.set_entry_point('validate_purity')
graph.add_edge('validate_purity', 'check_documentation')
graph.add_edge('check_documentation', END)
graph = graph.compile()
