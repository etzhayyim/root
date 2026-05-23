from typing import TypedDict, List
from langgraph.graph import StateGraph, END

class ForgingState(TypedDict):
    spec_data: dict
    validation_errors: List[str]
    is_approved: bool

def validate_material_grade(state: ForgingState):
    grade = state['spec_data'].get('grade')
    if not grade:
        state['validation_errors'].append('Missing alloy grade')
    return state

def check_tolerances(state: ForgingState):
    tol = state['spec_data'].get('tolerance')
    if tol and float(tol) > 0.05:
        state['validation_errors'].append('Tolerance exceeds limits')
    return state

graph = StateGraph(ForgingState)
graph.add_node('validate_material', validate_material_grade)
graph.add_node('check_dims', check_tolerances)
graph.set_entry_point('validate_material')
graph.add_edge('validate_material', 'check_dims')
graph.add_edge('check_dims', END)
graph = graph.compile()
