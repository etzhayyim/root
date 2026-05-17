from typing import TypedDict
from langgraph.graph import StateGraph, END
class CastingState(TypedDict):
    specs: dict
    validated: bool
    error: str
def validate_specs(state: CastingState):
    required = ['dimensional_tolerance', 'material_grade']
    valid = all(k in state['specs'] for k in required)
    return {'validated': valid, 'error': '' if valid else 'Missing specs'}
def finalize_procurement(state: CastingState):
    return {'validated': True}
graph = StateGraph(CastingState)
graph.add_node('validate', validate_specs)
graph.add_node('finish', finalize_procurement)
graph.add_edge('validate', 'finish')
graph.set_entry_point('validate')
graph.add_edge('finish', END)
graph = graph.compile()