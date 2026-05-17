from typing import TypedDict, List
from langgraph.graph import StateGraph, END

class PBXState(TypedDict):
    specs: dict
    validation_errors: List[str]
    is_approved: bool

def validate_specs(state: PBXState):
    errors = []
    if not state['specs'].get('sip_compatibility'):
        errors.append('SIP compatibility missing')
    return {'validation_errors': errors}

def approval_check(state: PBXState):
    return {'is_approved': len(state['validation_errors']) == 0}

graph = StateGraph(PBXState)
graph.add_node('validate', validate_specs)
graph.add_node('approve', approval_check)
graph.set_entry_point('validate')
graph.add_edge('validate', 'approve')
graph.add_edge('approve', END)
graph = graph.compile()