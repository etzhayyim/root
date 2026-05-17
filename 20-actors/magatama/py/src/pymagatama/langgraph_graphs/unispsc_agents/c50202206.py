from typing import TypedDict, List
from langgraph.graph import StateGraph, END

class SpiritState(TypedDict):
    product_info: dict
    validation_errors: List[str]
    is_compliant: bool

def validate_spirits(state: SpiritState):
    errors = []
    if state['product_info'].get('alcohol_content', 0) <= 0:
        errors.append('Invalid alcohol content')
    return {'validation_errors': errors, 'is_compliant': len(errors) == 0}

graph = StateGraph(SpiritState)
graph.add_node('validate', validate_spirits)
graph.set_entry_point('validate')
graph.add_edge('validate', END)
graph = graph.compile()