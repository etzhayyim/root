from typing import TypedDict
from langgraph.graph import StateGraph, END

class PlantModelState(TypedDict):
    model_type: str
    material: str
    is_verified: bool

def validate_model(state: PlantModelState) -> PlantModelState:
    state['is_verified'] = state['material'] in ['Resin', 'Silicone', 'High-Density Polymer']
    return state

def assembly_check(state: PlantModelState) -> PlantModelState:
    print(f'Checking assembly requirements for {state['model_type']}')
    return state

graph = StateGraph(PlantModelState)
graph.add_node('validate', validate_model)
graph.add_node('assembly', assembly_check)
graph.set_entry_point('validate')
graph.add_edge('validate', 'assembly')
graph.add_edge('assembly', END)
graph = graph.compile()