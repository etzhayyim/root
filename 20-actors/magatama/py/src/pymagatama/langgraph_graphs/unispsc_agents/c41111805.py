from typing import TypedDict
from langgraph.graph import StateGraph, END

class RadiographyState(TypedDict):
    source_activity: float
    has_license: bool
    safety_check_passed: bool

def validate_source(state: RadiographyState):
    print('Validating Co-60 source activity...')
    return {'safety_check_passed': state['source_activity'] > 0}

def verify_regulations(state: RadiographyState):
    print('Verifying nuclear regulatory licenses...')
    return {'has_license': True}

graph = StateGraph(RadiographyState)
graph.add_node('validate', validate_source)
graph.add_node('verify', verify_regulations)
graph.add_edge('validate', 'verify')
graph.add_edge('verify', END)
graph.set_entry_point('validate')
graph = graph.compile()