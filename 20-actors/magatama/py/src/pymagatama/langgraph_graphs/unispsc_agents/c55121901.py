from typing import TypedDict
from langgraph.graph import StateGraph, END

class AdvertisingState(TypedDict):
    spec_data: dict
    approved: bool

def validate_structural_specs(state: AdvertisingState):
    # Simulate structural CAD/safety check for outdoor pillars
    state['approved'] = state['spec_data'].get('wind_load_rating', 0) > 50
    return state

def procurement_decision(state: AdvertisingState):
    return 'proceed' if state['approved'] else 'refine_specs'

graph = StateGraph(AdvertisingState)
graph.add_node('validation', validate_structural_specs)
graph.set_entry_point('validation')
graph.add_edge('validation', END)
