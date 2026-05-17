from typing import TypedDict
from langgraph.graph import StateGraph, END

class State(TypedDict):
    part_specs: dict
    validation_log: list
    approved: bool

def validate_specs(state: State):
    specs = state['part_specs']
    logs = []
    if specs.get('heat_rating', 0) < 250:
        logs.append('Insufficient heat rating')
    return {'validation_log': logs, 'approved': len(logs) == 0}

graph = StateGraph(State)
graph.add_node('validator', validate_specs)
graph.set_entry_point('validator')
graph.add_edge('validator', END)
graph = graph.compile()