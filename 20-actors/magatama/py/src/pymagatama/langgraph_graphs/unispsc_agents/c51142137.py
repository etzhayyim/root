from typing import TypedDict, List
from langgraph.graph import StateGraph, END

class ChemState(TypedDict):
    material_name: str
    purity_level: float
    has_coa: bool
    is_compliant: bool

def validate_purity(state: ChemState):
    state['is_compliant'] = state['purity_level'] >= 99.0 and state['has_coa']
    return state

def check_storage(state: ChemState):
    print('Verifying cold chain logistics for Indomethacin...')
    return state

graph = StateGraph(ChemState)
graph.add_node('Validate', validate_purity)
graph.add_node('Storage', check_storage)
graph.set_entry_point('Validate')
graph.add_edge('Validate', 'Storage')
graph.add_edge('Storage', END)
graph = graph.compile()
