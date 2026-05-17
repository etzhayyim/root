from typing import TypedDict
from langgraph.graph import StateGraph, END

class HeatExchangerState(TypedDict):
    pressure_rating: float
    material_certified: bool
    validation_passed: bool

def validate_specs(state: HeatExchangerState):
    state['validation_passed'] = state['pressure_rating'] > 0 and state['material_certified']
    return state

def route_procurement(state: HeatExchangerState):
    return 'approve' if state['validation_passed'] else 'reject'

graph = StateGraph(HeatExchangerState)
graph.add_node('validator', validate_specs)
graph.set_entry_point('validator')
graph.add_edge('validator', END)
graph.compile()