from typing import TypedDict
from langgraph.graph import StateGraph, END

class AttireState(TypedDict):
    spec_data: dict
    approved: bool

def validate_materials(state: AttireState):
    # Business logic for textile safety standards in food prep
    is_valid = state['spec_data'].get('antimicrobial', False)
    return {'approved': is_valid}

graph = StateGraph(AttireState)
graph.add_node('validate', validate_materials)
graph.set_entry_point('validate')
graph.add_edge('validate', END)
graph = graph.compile()
