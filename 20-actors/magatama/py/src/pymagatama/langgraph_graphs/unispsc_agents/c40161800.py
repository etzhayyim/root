from typing import TypedDict
from langgraph.graph import StateGraph, END

class FilterMediaState(TypedDict):
    material_type: str
    micron_rating: float
    compatibility_check: bool
    is_approved: bool

def validate_materials(state: FilterMediaState):
    # Business logic for filter media chemical compatibility validation
    state['compatibility_check'] = state['material_type'] in ['polypropylene', 'glass-fiber', 'cellulose']
    return state

def evaluate_specs(state: FilterMediaState):
    # Logic to verify rating against industrial standards
    state['is_approved'] = state['compatibility_check'] and state['micron_rating'] > 0
    return state

graph = StateGraph(FilterMediaState)
graph.add_node('validate', validate_materials)
graph.add_node('evaluate', evaluate_specs)
graph.set_entry_point('validate')
graph.add_edge('validate', 'evaluate')
graph.add_edge('evaluate', END)

compiled_graph = graph.compile()
