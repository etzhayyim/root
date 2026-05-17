from typing import TypedDict
from langgraph.graph import StateGraph, END

class PipeState(TypedDict):
    spec_data: dict
    validation_passed: bool

def validate_materials(state: PipeState):
    grade = state['spec_data'].get('material_grade')
    state['validation_passed'] = grade in ['SS400', 'STKM13A']
    return state

def check_pressure_spec(state: PipeState):
    rating = state['spec_data'].get('pressure_rating', 0)
    valid = rating > 0
    state['validation_passed'] = state['validation_passed'] and valid
    return state

graph = StateGraph(PipeState)
graph.add_node('validate', validate_materials)
graph.add_node('pressure_check', check_pressure_spec)
graph.set_entry_point('validate')
graph.add_edge('validate', 'pressure_check')
graph.add_edge('pressure_check', END)
graph = graph.compile()