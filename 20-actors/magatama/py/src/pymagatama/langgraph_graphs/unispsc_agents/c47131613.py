from typing import TypedDict, List
from langgraph.graph import StateGraph, END

class MopHolderState(TypedDict):
    specs: dict
    validation_errors: List[str]
    is_approved: bool

def validate_specs(state: MopHolderState):
    errors = []
    if not state['specs'].get('load_capacity'): errors.append('Missing load capacity')
    if not state['specs'].get('mounting_type'): errors.append('Missing mounting type')
    return {'validation_errors': errors, 'is_approved': len(errors) == 0}

graph = StateGraph(MopHolderState)
graph.add_node('validate', validate_specs)
graph.set_entry_point('validate')
graph.add_edge('validate', END)
graph = graph.compile()
