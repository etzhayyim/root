from typing import TypedDict, List
from langgraph.graph import StateGraph, END

class CraftState(TypedDict):
    specs: dict
    validation_errors: List[str]
    is_approved: bool

def validate_material(state: CraftState):
    errors = []
    if 'material' not in state['specs']: errors.append('Missing material type')
    return {'validation_errors': errors}

def check_compliance(state: CraftState):
    approved = len(state['validation_errors']) == 0
    return {'is_approved': approved}

graph = StateGraph(CraftState)
graph.add_node('validate', validate_material)
graph.add_node('compliance', check_compliance)
graph.add_edge('validate', 'compliance')
graph.add_edge('compliance', END)
graph.set_entry_point('validate')
app = graph.compile()
