from typing import TypedDict, List
from langgraph.graph import StateGraph, END

class TubeState(TypedDict):
    specs: dict
    validated: bool
    error: str

def validate_medical_specs(state: TubeState):
    required = ['material_biocompatibility_iso10993', 'sterile_certification']
    if all(k in state['specs'] for k in required):
        return {'validated': True}
    return {'validated': False, 'error': 'Missing mandatory medical certifications'}

def route_verification(state: TubeState):
    return 'pass' if state['validated'] else 'fail'

graph = StateGraph(TubeState)
graph.add_node('validation', validate_medical_specs)
graph.add_edge('validation', END)
graph.set_entry_point('validation')
graph = graph.compile()
