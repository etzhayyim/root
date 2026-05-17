from typing import TypedDict
from langgraph.graph import StateGraph, END

class ProcurementState(TypedDict):
    specs: dict
    validated: bool
    error: str

def validate_materials(state: ProcurementState):
    alloy = state['specs'].get('alloy', 'Unknown')
    is_valid = alloy in ['6061-T6', '7075-T6']
    return {'validated': is_valid, 'error': '' if is_valid else 'Invalid material grade'}

def assembly_check(state: ProcurementState):
    if state.get('validated'):
        return {'validated': True}
    return {'validated': False}

graph = StateGraph(ProcurementState)
graph.add_node('validate', validate_materials)
graph.add_node('check', assembly_check)
graph.set_entry_point('validate')
graph.add_edge('validate', 'check')
graph.add_edge('check', END)
graph = graph.compile()