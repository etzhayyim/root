from typing import TypedDict
from langgraph.graph import StateGraph, END

class State(TypedDict):
    device_specs: dict
    compliance_ok: bool

def validate_specs(state: State):
    reqs = ['weight_limit', 'safety_certification']
    state['compliance_ok'] = all(k in state['device_specs'] for k in reqs)
    return state

graph = StateGraph(State)
graph.add_node('validate', validate_specs)
graph.set_entry_point('validate')
graph.add_edge('validate', END)
graph = graph.compile()