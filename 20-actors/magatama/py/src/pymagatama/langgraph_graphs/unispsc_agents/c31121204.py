from typing import TypedDict, List
from langgraph.graph import StateGraph, END

class CastState(TypedDict):
    spec_sheet: dict
    validation_errors: List[str]
    is_compliant: bool

def validate_material(state: CastState):
    grade = state['spec_sheet'].get('grade')
    if not grade: return {'validation_errors': ['Missing material grade']}
    return {'is_compliant': True}

def inspect_dimensions(state: CastState):
    if state['spec_sheet'].get('tolerance', 0) > 0.05:
        return {'validation_errors': ['Tolerance exceeds specification limit']}
    return {'is_compliant': True}

graph = StateGraph(CastState)
graph.add_node('validate', validate_material)
graph.add_node('inspect', inspect_dimensions)
graph.set_entry_point('validate')
graph.add_edge('validate', 'inspect')
graph.add_edge('inspect', END)
graph = graph.compile()