from typing import TypedDict
from langgraph.graph import StateGraph, END

class ToiletSpecState(TypedDict):
    spec_data: dict
    validation_errors: list
    is_compliant: bool

def validate_plumbing_specs(state: ToiletSpecState):
    errs = []
    if state['spec_data'].get('flush_volume', 0) > 6:
        errs.append('Exceeds max flush limit')
    return {'validation_errors': errs, 'is_compliant': len(errs) == 0}

graph = StateGraph(ToiletSpecState)
graph.add_node('validate', validate_plumbing_specs)
graph.set_entry_point('validate')
graph.add_edge('validate', END)
graph = graph.compile()
