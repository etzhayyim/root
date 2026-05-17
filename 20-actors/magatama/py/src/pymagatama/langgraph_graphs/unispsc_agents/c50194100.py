from typing import TypedDict, List
from langgraph.graph import StateGraph, END

class CitrusState(TypedDict):
    product_info: dict
    quality_checks: List[str]
    approved: bool

def validate_purity(state: CitrusState):
    checks = state.get('quality_checks', [])
    if 'Brix' in state['product_info'] and 'pH' in state['product_info']:
        checks.append('Chemical Specs ValidATED')
    return {'quality_checks': checks}

def check_storage(state: CitrusState):
    is_ok = state['product_info'].get('temp') == 'frozen'
    return {'approved': is_ok}

graph = StateGraph(CitrusState)
graph.add_node('validate', validate_purity)
graph.add_node('storage', check_storage)
graph.add_edge('validate', 'storage')
graph.add_edge('storage', END)
graph.set_entry_point('validate')
graph = graph.compile()