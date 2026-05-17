from typing import TypedDict
from langgraph.graph import StateGraph, END

class StereoscopeState(TypedDict):
    spec_data: dict
    is_compliant: bool
    validation_log: list

def validate_specs(state: StereoscopeState):
    log = []
    required = ['magnification', 'led_intensity']
    valid = all(k in state['spec_data'] for k in required)
    log.append('Specs validated') if valid else log.append('Specs missing')
    return {'is_compliant': valid, 'validation_log': log}

def update_status(state: StereoscopeState):
    return {'validation_log': state['validation_log'] + ['Status updated']}

graph = StateGraph(StereoscopeState)
graph.add_node('validate', validate_specs)
graph.add_node('update', update_status)
graph.set_entry_point('validate')
graph.add_edge('validate', 'update')
graph.add_edge('update', END)
graph = graph.compile()