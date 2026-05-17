from typing import TypedDict, List
from langgraph.graph import StateGraph, END

class NeedleState(TypedDict):
    specifications: dict
    validation_errors: List[str]
    approved: bool

def validate_needle_specs(state: NeedleState):
    errors = []
    if 'material' not in state['specifications']:
        errors.append('Missing material specification')
    if 'gauge' not in state['specifications']:
        errors.append('Missing needle gauge size')
    return {'validation_errors': errors, 'approved': len(errors) == 0}

graph = StateGraph(NeedleState)
graph.add_node('validate', validate_needle_specs)
graph.set_entry_point('validate')
graph.add_edge('validate', END)
app = graph.compile()