from typing import TypedDict
from langgraph.graph import StateGraph, END

class TheaterState(TypedDict):
    specs: dict
    is_compliant: bool

def validate_aseptic_standards(state: TheaterState):
    air_rate = state['specs'].get('air_exchange_rate', 0)
    state['is_compliant'] = air_rate >= 20
    return state

def review_safety_protocols(state: TheaterState):
    print('Verifying sterile compliance for operating theater...')
    return state

graph = StateGraph(TheaterState)
graph.add_node('validate', validate_aseptic_standards)
graph.add_node('review', review_safety_protocols)
graph.add_edge('validate', 'review')
graph.add_edge('review', END)
graph.set_entry_point('validate')
app = graph.compile()