from typing import TypedDict
from langgraph.graph import StateGraph, END

class BiosphereState(TypedDict):
    biosphere_id: str
    contents: list
    status: str
    is_viable: bool

def validate_stability(state: BiosphereState):
    # Simulate biological stability check
    state['is_viable'] = all(item != 'invasive' for item in state['contents'])
    return {'status': 'validated' if state['is_viable'] else 'rejected'}

def check_integrity(state: BiosphereState):
    # Simulate physical containment inspection
    return {'status': 'ready_for_dispatch'}

graph = StateGraph(BiosphereState)
graph.add_node('validate', validate_stability)
graph.add_node('integrity_check', check_integrity)
graph.set_entry_point('validate')
graph.add_edge('validate', 'integrity_check')
graph.add_edge('integrity_check', END)
graph.compile()
