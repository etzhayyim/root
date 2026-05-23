from typing import TypedDict
from langgraph.graph import StateGraph, END

class JumperState(TypedDict):
    spec: dict
    is_compliant: bool

def validate_specs(state: JumperState):
    required = ['gauge', 'voltage', 'termination']
    valid = all(k in state['spec'] for k in required)
    return {'is_compliant': valid}

graph = StateGraph(JumperState)
graph.add_node('validate', validate_specs)
graph.set_entry_point('validate')
graph.add_edge('validate', END)
graph = graph.compile()
