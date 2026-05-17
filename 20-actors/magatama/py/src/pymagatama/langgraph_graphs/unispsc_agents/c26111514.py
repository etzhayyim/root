from langgraph.graph import StateGraph, END
from typing import TypedDict, List

class JointState(TypedDict):
    spec_sheet: dict
    validation_errors: List[str]
    is_approved: bool

def validate_material(state: JointState):
    errors = []
    if 'material' not in state['spec_sheet']: errors.append('Missing material spec')
    return {'validation_errors': errors}

def check_load_capacity(state: JointState):
    if state['spec_sheet'].get('load_capacity', 0) < 0: state['is_approved'] = False
    return state

graph = StateGraph(JointState)
graph.add_node('validate', validate_material)
graph.add_node('load_check', check_load_capacity)
graph.set_entry_point('validate')
graph.add_edge('validate', 'load_check')
graph.add_edge('load_check', END)
graph = graph.compile()