from typing import TypedDict
from langgraph.graph import StateGraph, END

class ConnectorState(TypedDict):
    spec_data: dict
    validated: bool

def validate_specs(state: ConnectorState):
    required = ['wire_gauge', 'material']
    return {'validated': all(k in state['spec_data'] for k in required)}

def compile_graph():
    graph = StateGraph(ConnectorState)
    graph.add_node('validation', validate_specs)
    graph.set_entry_point('validation')
    graph.add_edge('validation', END)
    return graph.compile()

graph = compile_graph()
