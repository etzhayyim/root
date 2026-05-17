from typing import TypedDict
from langgraph.graph import StateGraph, END

class FilterSpecState(TypedDict):
    material: str
    micron_rating: float
    valid: bool

def validate_spec(state: FilterSpecState):
    # Business logic for filter cloth inspection criteria
    if state['micron_rating'] > 0 and state['material']:
        return {'valid': True}
    return {'valid': False}

def process_procurement(state: FilterSpecState):
    return {f'status': 'Validated' if state['valid'] else 'Rejected'}

graph = StateGraph(FilterSpecState)
graph.add_node('validate', validate_spec)
graph.add_node('process', process_procurement)
graph.add_edge('validate', 'process')
graph.add_edge('process', END)
graph.set_entry_point('validate')
graph = graph.compile()