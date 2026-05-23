from typing import TypedDict
from langgraph.graph import StateGraph, END

class TowelState(TypedDict):
    gsm: int
    material: str
    is_compliant: bool

def validate_towel_specs(state: TowelState):
    # Business logic for textile quality control
    if state['gsm'] >= 400 and state['material'] in ['Cotton', 'Bamboo']:
        return {**state, 'is_compliant': True}
    return {**state, 'is_compliant': False}

graph = StateGraph(TowelState)
graph.add_node('validate', validate_towel_specs)
graph.set_entry_point('validate')
graph.add_edge('validate', END)
graph = graph.compile()
