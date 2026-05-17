from typing import TypedDict, List
from langgraph.graph import StateGraph, END

class ExtrusionState(TypedDict):
    specs: dict
    validation_passed: bool
    error_log: List[str]

def validate_materials(state: ExtrusionState):
    grade = state['specs'].get('material_grade')
    if not grade: return {'validation_passed': False, 'error_log': ['Missing Material Grade']}
    return {'validation_passed': True}

def check_tolerances(state: ExtrusionState):
    if state['specs'].get('tolerance', 0) > 0.05:
        return {'validation_passed': False, 'error_log': ['Tolerance exceeds limits']}
    return {'validation_passed': True}

graph = StateGraph(ExtrusionState)
graph.add_node('material_check', validate_materials)
graph.add_node('tolerance_check', check_tolerances)
graph.set_entry_point('material_check')
graph.add_edge('material_check', 'tolerance_check')
graph.add_edge('tolerance_check', END)
graph = graph.compile()