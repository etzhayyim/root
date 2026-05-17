from typing import TypedDict
from langgraph.graph import StateGraph, END

class State(TypedDict):
    spec_data: dict
    validation_log: list
    status: str

def validate_specs(state: State):
    reqs = state['spec_data']
    log = []
    if 'load_capacity' not in reqs:
        log.append('Missing load capacity specification')
    return {'validation_log': log, 'status': 'valid' if not log else 'invalid'}

graph = StateGraph(State)
graph.add_node('validate', validate_specs)
graph.set_entry_point('validate')
graph.add_edge('validate', END)
graph = graph.compile()