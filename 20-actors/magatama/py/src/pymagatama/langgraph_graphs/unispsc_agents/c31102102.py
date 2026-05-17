from typing import TypedDict, List
from langgraph.graph import StateGraph, END

class CastingState(TypedDict):
    part_specs: dict
    validation_passed: bool
    error_log: List[str]

def validate_materials(state: CastingState):
    grade = state['part_specs'].get('alloy_grade')
    if not grade: return {'validation_passed': False, 'error_log': ['Missing alloy grade']}
    return {'validation_passed': True}

def check_tolerances(state: CastingState):
    tolerances = state['part_specs'].get('tolerances', {})
    if tolerances.get('critical_dimension', 0) > 0.05:
        return {'validation_passed': False}
    return {'validation_passed': True}

graph = StateGraph(CastingState)
graph.add_node('material_check', validate_materials)
graph.add_node('tolerance_check', check_tolerances)
graph.set_entry_point('material_check')
graph.add_edge('material_check', 'tolerance_check')
graph.add_edge('tolerance_check', END)
graph = graph.compile()