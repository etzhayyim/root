from langgraph.graph import StateGraph, END
from typing import TypedDict, List

class ShuffleboardState(TypedDict):
    specs: dict
    validation_errors: List[str]
    is_approved: bool

def validate_dimensions(state: ShuffleboardState):
    length = state['specs'].get('length', 0)
    if length < 9 or length > 22:
        state['validation_errors'].append('Invalid board length')
    return state

def check_quality_compliance(state: ShuffleboardState):
    if state['specs'].get('material') != 'hardwood':
        state['validation_errors'].append('Non-compliant surface material')
    else:
        state['is_approved'] = True
    return state

graph = StateGraph(ShuffleboardState)
graph.add_node('validate', validate_dimensions)
graph.add_node('compliance', check_quality_compliance)
graph.set_entry_point('validate')
graph.add_edge('validate', 'compliance')
graph.add_edge('compliance', END)
graph = graph.compile()
