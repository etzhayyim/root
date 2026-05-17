from typing import TypedDict, List
from langgraph.graph import StateGraph, END

class SterilizationSpecState(TypedDict):
    spec_id: str
    material: str
    max_temp: float
    validated: bool

def validate_material(state: SterilizationSpecState):
    # Simulate material compliance check against medical standards
    state['validated'] = state['material'] in ['Stainless Steel', 'Polyetheretherketone']
    return state

def check_thermal_limit(state: SterilizationSpecState):
    # Ensure plate withstands 135C autoclave cycles
    state['validated'] = state['validated'] and (state['max_temp'] >= 135.0)
    return state

graph = StateGraph(SterilizationSpecState)
graph.add_node('val_mat', validate_material)
graph.add_node('val_temp', check_thermal_limit)
graph.set_entry_point('val_mat')
graph.add_edge('val_mat', 'val_temp')
graph.add_edge('val_temp', END)

graph = graph.compile()