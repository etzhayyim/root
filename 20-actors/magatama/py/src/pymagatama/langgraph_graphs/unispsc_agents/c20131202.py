from typing import TypedDict
from langgraph.graph import StateGraph, END

class HexNutState(TypedDict):
    spec_data: dict
    approved: bool

def validate_specs(state: HexNutState):
    specs = state['spec_data']
    is_valid = 'Material Grade' in specs and 'Thread Pitch' in specs
    return {'approved': is_valid}

graph = StateGraph(HexNutState)
graph.add_node('validator', validate_specs)
graph.set_entry_point('validator')
graph.add_edge('validator', END)
graph = graph.compile()