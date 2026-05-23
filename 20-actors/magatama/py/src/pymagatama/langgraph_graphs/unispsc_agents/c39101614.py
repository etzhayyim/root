from typing import TypedDict, List
from langgraph.graph import StateGraph, END

class LampState(TypedDict):
    specs: dict
    validation_errors: List[str]
    approved: bool

def validate_lamp_specs(state: LampState):
    errors = []
    if state['specs'].get('mercury_content_mg', 0) > 50:
        errors.append('Exceeds mercury content threshold')
    return {'validation_errors': errors, 'approved': len(errors) == 0}

graph = StateGraph(LampState)
graph.add_node('validate', validate_lamp_specs)
graph.set_entry_point('validate')
graph.add_edge('validate', END)
graph = graph.compile()
