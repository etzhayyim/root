from typing import TypedDict
from langgraph.graph import StateGraph, END

class TapeState(TypedDict):
    specs: dict
    approved: bool

def validate_conductivity(state: TapeState):
    resistance = state['specs'].get('surface_resistivity', 100)
    state['approved'] = resistance < 500
    return state

def check_thermal(state: TapeState):
    temp = state['specs'].get('thermal_rating', 0)
    state['approved'] = state['approved'] and (temp > 80)
    return state

graph = StateGraph(TapeState)
graph.add_node('validate_conductivity', validate_conductivity)
graph.add_node('check_thermal', check_thermal)
graph.set_entry_point('validate_conductivity')
graph.add_edge('validate_conductivity', 'check_thermal')
graph.add_edge('check_thermal', END)

graph = graph.compile()