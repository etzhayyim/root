from typing import TypedDict, List
from langgraph.graph import StateGraph, END

class LecternComponentState(TypedDict):
    component_name: str
    specs: dict
    approved: bool
    validation_errors: List[str]

def validate_specs(state: LecternComponentState):
    errors = []
    if 'voltage' not in state['specs']: errors.append('Missing voltage')
    if 'safety_compliance' not in state['specs']: errors.append('Missing safety cert')
    return {'validation_errors': errors, 'approved': len(errors) == 0}

graph = StateGraph(LecternComponentState)
graph.add_node('validate', validate_specs)
graph.set_entry_point('validate')
graph.add_edge('validate', END)
graph = graph.compile()
