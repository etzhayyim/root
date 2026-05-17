from langgraph.graph import StateGraph, END
from typing import TypedDict
class CarpetState(TypedDict):
    spec: dict
    validated: bool
def validate_spec(state: CarpetState):
    required = ['thickness_mm', 'flammability_rating']
    valid = all(k in state['spec'] for k in required)
    return {'validated': valid}
def finalize(state: CarpetState):
    return {'validated': True}
graph = StateGraph(CarpetState)
graph.add_node('validate', validate_spec)
graph.add_node('finalize', finalize)
graph.add_edge('validate', 'finalize')
graph.add_edge('finalize', END)
graph.set_entry_point('validate')
graph = graph.compile()