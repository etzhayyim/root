from langgraph.graph import StateGraph, END
from typing import TypedDict, List

class WasherState(TypedDict):
    spec_data: dict
    validation_passed: bool
    error_log: List[str]

def validate_material(state: WasherState):
    grade = state['spec_data'].get('material', '')
    return {'validation_passed': grade in ['304', '316', 'Carbon Steel'], 'error_log': [] if grade else ['Missing material grade']}

def check_dimensions(state: WasherState):
    tol = state['spec_data'].get('tolerance', 0.05)
    return {'validation_passed': state['validation_passed'] and (tol <= 0.1)}

graph = StateGraph(WasherState)
graph.add_node('validate_material', validate_material)
graph.add_node('check_dimensions', check_dimensions)
graph.set_entry_point('validate_material')
graph.add_edge('validate_material', 'check_dimensions')
graph.add_edge('check_dimensions', END)
app = graph.compile()