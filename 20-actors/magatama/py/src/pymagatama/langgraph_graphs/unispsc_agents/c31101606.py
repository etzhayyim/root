from typing import TypedDict
from langgraph.graph import StateGraph, END

class CastingState(TypedDict):
    specs: dict
    validation_log: list
    is_approved: bool

def validate_specs(state: CastingState):
    log = []
    if 'Material Grade' not in state['specs']:
        log.append('Missing Material Grade')
    return {'validation_log': log}

def check_compliance(state: CastingState):
    approved = len(state['validation_log']) == 0
    return {'is_approved': approved}

graph = StateGraph(CastingState)
graph.add_node('validate', validate_specs)
graph.add_node('compliance', check_compliance)
graph.set_entry_point('validate')
graph.add_edge('validate', 'compliance')
graph.add_edge('compliance', END)
graph = graph.compile()