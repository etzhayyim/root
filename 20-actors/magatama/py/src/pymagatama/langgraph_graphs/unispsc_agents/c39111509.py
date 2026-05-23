from typing import TypedDict, List
from langgraph.graph import StateGraph, END

class LampSpecState(TypedDict):
    specs: dict
    validation_errors: List[str]
    approved: bool

def validate_lamp_specs(state: LampSpecState):
    errors = []
    if state['specs'].get('power_consumption_watts', 0) > 100:
        errors.append('High power consumption exceeds standard limit')
    if not state['specs'].get('safety_certification_standards'):
        errors.append('Missing mandatory safety certifications')
    return {'validation_errors': errors, 'approved': len(errors) == 0}

graph = StateGraph(LampSpecState)
graph.add_node('validate', validate_lamp_specs)
graph.set_entry_point('validate')
graph.add_edge('validate', END)
graph = graph.compile()
