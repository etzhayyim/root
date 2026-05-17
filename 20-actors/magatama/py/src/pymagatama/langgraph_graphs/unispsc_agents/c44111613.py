from typing import TypedDict
from langgraph.graph import StateGraph, END

class CardHolderState(TypedDict):
    spec_data: dict
    validation_errors: list
    status: str

def validate_specs(state: CardHolderState):
    errors = []
    if not state['spec_data'].get('material_type'): errors.append('Missing material_type')
    return {'validation_errors': errors, 'status': 'validated' if not errors else 'failed'}

def approve_order(state: CardHolderState):
    return {'status': 'approved'}

graph = StateGraph(CardHolderState)
graph.add_node('validator', validate_specs)
graph.add_node('approver', approve_order)
graph.set_entry_point('validator')
graph.add_edge('validator', 'approver')
graph.add_edge('approver', END)
compile_graph = graph.compile()