from typing import TypedDict
from langgraph.graph import StateGraph, END

class VetFurnitureState(TypedDict):
    specs: dict
    validated: bool

def validate_specs(state: VetFurnitureState):
    required = ['Material', 'WeightLimit']
    valid = all(k in state['specs'] for k in required)
    return {'validated': valid}

def route_verification(state: VetFurnitureState):
    return 'validate' if not state.get('validated') else END

graph = StateGraph(VetFurnitureState)
graph.add_node('validate', validate_specs)
graph.set_entry_point('validate')
graph.add_edge('validate', END)
graph.compile()
