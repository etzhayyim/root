from typing import TypedDict
from langgraph.graph import StateGraph, END

class EnclosureState(TypedDict):
    specs: dict
    validated: bool

def validate_specs(state: EnclosureState):
    required = ['IP Rating', 'Material Grade']
    return {'validated': all(k in state['specs'] for k in required)}

def finalize_order(state: EnclosureState):
    return {'validated': True}

graph = StateGraph(EnclosureState)
graph.add_node('validate', validate_specs)
graph.add_node('finalize', finalize_order)
graph.set_entry_point('validate')
graph.add_edge('validate', 'finalize')
graph.add_edge('finalize', END)
graph = graph.compile()