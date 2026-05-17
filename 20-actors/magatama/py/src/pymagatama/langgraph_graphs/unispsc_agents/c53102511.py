from langgraph.graph import StateGraph, END
from typing import TypedDict, List

class BandanaState(TypedDict):
    specs: dict
    validation_errors: List[str]
    is_approved: bool

def validate_materials(state: BandanaState):
    """Validates fabric type and chemical compliance."""
    errors = []
    if state['specs'].get('material') not in ['cotton', 'polyester', 'blend']:
        errors.append('Invalid material type')
    return {'validation_errors': errors}

def final_check(state: BandanaState):
    """Determines if approval threshold is met."""
    return {'is_approved': len(state['validation_errors']) == 0}

graph = StateGraph(BandanaState)
graph.add_node('validate', validate_materials)
graph.add_node('approval', final_check)
graph.set_entry_point('validate')
graph.add_edge('validate', 'approval')
graph.add_edge('approval', END)
graph = graph.compile()