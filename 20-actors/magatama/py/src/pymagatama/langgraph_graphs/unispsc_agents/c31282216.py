from typing import TypedDict, List
from langgraph.graph import StateGraph, END

class SteelComponentState(TypedDict):
    spec_sheet: dict
    validation_errors: List[str]
    approved: bool

def validate_specs(state: SteelComponentState):
    errors = []
    if state['spec_sheet'].get('tensile_strength_mpa', 0) < 400:
        errors.append('Insufficient tensile strength for industrial application')
    return {'validation_errors': errors, 'approved': len(errors) == 0}

graph = StateGraph(SteelComponentState)
graph.add_node('validate', validate_specs)
graph.set_entry_point('validate')
graph.add_edge('validate', END)
graph = graph.compile()