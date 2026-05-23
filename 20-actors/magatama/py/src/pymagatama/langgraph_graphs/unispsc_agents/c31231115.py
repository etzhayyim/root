from typing import TypedDict
from langgraph.graph import StateGraph, END

class AlloyState(TypedDict):
    specs: dict
    validated: bool
    compliant: bool

def validate_materials(state: AlloyState):
    grade = state['specs'].get('grade')
    state['validated'] = grade is not None
    return state

def check_compliance(state: AlloyState):
    state['compliant'] = state['validated'] and state['specs'].get('tensile_strength', 0) > 400
    return state

graph = StateGraph(AlloyState)
graph.add_node('validate', validate_materials)
graph.add_node('compliance', check_compliance)
graph.set_entry_point('validate')
graph.add_edge('validate', 'compliance')
graph.add_edge('compliance', END)
graph = graph.compile()
