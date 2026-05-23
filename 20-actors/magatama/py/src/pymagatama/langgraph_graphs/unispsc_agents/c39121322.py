from typing import TypedDict, List
from langgraph.graph import StateGraph, END

class PartitionState(TypedDict):
    specs: dict
    validation_errors: List[str]
    is_approved: bool

def validate_dimensions(state: PartitionState):
    """Validates partition dimensions against box requirement"""
    if state['specs'].get('dim_match', False):
        return {'validation_errors': []}
    return {'validation_errors': ['Dimension mismatch detected']}

def check_fire_rating(state: PartitionState):
    """Ensures material meets fire safety standards"""
    rating = state['specs'].get('fire_rating', 'None')
    if rating != 'UL94V-0':
         return {'validation_errors': state['validation_errors'] + ['Fire rating substandard']}
    return {'is_approved': True}

graph = StateGraph(PartitionState)
graph.add_node('validate', validate_dimensions)
graph.add_node('safety_check', check_fire_rating)
graph.set_entry_point('validate')
graph.add_edge('validate', 'safety_check')
graph.add_edge('safety_check', END)
graph = graph.compile()
