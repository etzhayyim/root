from typing import TypedDict
from langgraph.graph import StateGraph, END

class JumperState(TypedDict):
    specs: dict
    validated: bool

def validate_specs(state: JumperState):
    required = ['current_rating', 'pitch']
    return {'validated': all(k in state['specs'] for k in required)}

graph = StateGraph(JumperState)
graph.add_node('validate', validate_specs)
graph.set_entry_point('validate')
graph.add_edge('validate', END)
graph = graph.compile()