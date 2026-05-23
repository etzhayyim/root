from typing import TypedDict
from langgraph.graph import StateGraph, END

class ExtrusionState(TypedDict):
    specs: dict
    validation_passed: bool
    error_log: list

def validate_material_grade(state: ExtrusionState):
    grade = state['specs'].get('grade')
    if not grade: return {'validation_passed': False, 'error_log': ['Missing Grade']}
    return {'validation_passed': True}

def check_tolerances(state: ExtrusionState):
    tol = state['specs'].get('tolerance')
    return {'validation_passed': tol == 'precision'}

graph = StateGraph(ExtrusionState)
graph.add_node('material', validate_material_grade)
graph.add_node('tolerances', check_tolerances)
graph.set_entry_point('material')
graph.add_edge('material', 'tolerances')
graph.add_edge('tolerances', END)
app = graph.compile()
