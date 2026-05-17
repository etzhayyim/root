from typing import TypedDict
from langgraph.graph import StateGraph, END

class SignageState(TypedDict):
    specs: dict
    validation_log: list
    approved: bool

def validate_specs(state: SignageState):
    log = []
    if state['specs'].get('brightness', 0) < 500:
        log.append('Brightness insufficient for outdoor')
    return {'validation_log': log, 'approved': len(log) == 0}

graph = StateGraph(SignageState)
graph.add_node('validate', validate_specs)
graph.set_entry_point('validate')
graph.add_edge('validate', END)
graph = graph.compile()