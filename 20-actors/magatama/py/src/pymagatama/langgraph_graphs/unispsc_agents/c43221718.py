from langgraph.graph import StateGraph, END
from typing import TypedDict, List

class RadarState(TypedDict):
    specs: dict
    validation_errors: List[str]
    approved: bool

def validate_specs(state: RadarState):
    errors = []
    if 'frequency' not in state['specs']: errors.append('Missing frequency')
    return {'validation_errors': errors}

def export_check(state: RadarState):
    is_restricted = state['specs'].get('is_dual_use', False)
    return {'approved': not is_restricted}

graph = StateGraph(RadarState)
graph.add_node('validate', validate_specs)
graph.add_node('export_review', export_check)
graph.add_edge('validate', 'export_review')
graph.add_edge('export_review', END)
graph.set_entry_point('validate')
graph = graph.compile()
