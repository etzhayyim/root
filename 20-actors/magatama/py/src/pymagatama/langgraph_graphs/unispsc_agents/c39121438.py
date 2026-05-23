from typing import TypedDict
from langgraph.graph import StateGraph, END

class ConnectorState(TypedDict):
    specs: dict
    approved: bool

def validate_specs(state: ConnectorState):
    required = ['voltage', 'amperage', 'wire_gauge']
    state['approved'] = all(k in state['specs'] for k in required)
    return state

def routing(state: ConnectorState):
    return 'approved' if state['approved'] else 'rejected'

graph = StateGraph(ConnectorState)
graph.add_node('validate', validate_specs)
graph.set_entry_point('validate')
graph.add_edge('validate', END)
app = graph.compile()
