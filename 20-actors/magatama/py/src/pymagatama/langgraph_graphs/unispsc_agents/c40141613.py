from langgraph.graph import StateGraph, END
from typing import TypedDict, List

class ValveState(TypedDict):
    specs: dict
    validation_errors: List[str]
    approved: bool

def validate_pressure_rating(state: ValveState) -> ValveState:
    rating = state['specs'].get('pressure_rating_class')
    if not rating: state['validation_errors'].append('Missing pressure rating'); state['approved'] = False
    return state

def validate_materials(state: ValveState) -> ValveState:
    if 'body_material' not in state['specs']: state['validation_errors'].append('Missing material info')
    return state

graph = StateGraph(ValveState)
graph.add_node('check_pressure', validate_pressure_rating)
graph.add_node('check_materials', validate_materials)
graph.set_entry_point('check_pressure')
graph.add_edge('check_pressure', 'check_materials')
graph.add_edge('check_materials', END)
graph = graph.compile()
