from typing import TypedDict
from langgraph.graph import StateGraph, END

class SofaState(TypedDict):
    specs: dict
    approved: bool

def validate_specs(state: SofaState):
    required = ['dimensions', 'fire_standard']
    all_present = all(k in state['specs'] for k in required)
    return {'approved': all_present}

graph = StateGraph(SofaState)
graph.add_node('validate', validate_specs)
graph.set_entry_point('validate')
graph.add_edge('validate', END)
graph = graph.compile()