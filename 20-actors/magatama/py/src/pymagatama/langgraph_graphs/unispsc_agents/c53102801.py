from typing import TypedDict, List
from langgraph.graph import StateGraph, END

class SwimwearState(TypedDict):
    specs: dict
    approved: bool
    validation_errors: List[str]

def validate_materials(state: SwimwearState):
    errors = []
    if 'material' not in state['specs']: errors.append('Missing material info')
    return {'validation_errors': errors}

def check_compliance(state: SwimwearState):
    is_valid = len(state['validation_errors']) == 0
    return {'approved': is_valid}

graph = StateGraph(SwimwearState)
graph.add_node('validate', validate_materials)
graph.add_node('compliance', check_compliance)
graph.add_edge('validate', 'compliance')
graph.add_edge('compliance', END)
graph.set_entry_point('validate')
process = graph.compile()