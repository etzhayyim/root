from typing import TypedDict
from langgraph.graph import StateGraph, END

class State(TypedDict):
    purity_cert: bool
    temp_log: bool
    compliant: bool

def validate_api(state: State):
    is_compliant = state['purity_cert'] and state['temp_log']
    return {'compliant': is_compliant}

def router(state: State):
    return 'valid' if state['compliant'] else 'reject'

graph = StateGraph(State)
graph.add_node('validate', validate_api)
graph.add_edge('validate', END)
graph.set_entry_point('validate')
graph = graph.compile()
