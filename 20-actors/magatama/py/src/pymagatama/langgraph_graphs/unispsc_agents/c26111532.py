from typing import TypedDict, List
from langgraph.graph import StateGraph, END

class ShaftSupportState(TypedDict):
    specs: dict
    validation_errors: List[str]
    is_approved: bool

def validate_load_capacity(state: ShaftSupportState):
    load = state['specs'].get('load_capacity', 0)
    if load <= 0:
        state['validation_errors'].append('Invalid load capacity')
    return {'is_approved': len(state['validation_errors']) == 0}

def structural_integrity_check(state: ShaftSupportState):
    # Simulate CAD/FEA validation logic
    state['is_approved'] = state['is_approved'] and True
    return state

graph = StateGraph(ShaftSupportState)
graph.add_node('validate', validate_load_capacity)
graph.add_node('structural', structural_integrity_check)
graph.add_edge('validate', 'structural')
graph.add_edge('structural', END)
graph.set_entry_point('validate')
graph = graph.compile()
