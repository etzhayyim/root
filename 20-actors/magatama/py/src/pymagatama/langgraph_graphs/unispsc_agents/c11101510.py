from typing import TypedDict, Annotated, List
from langgraph.graph import StateGraph, END

class CoalProcessingState(TypedDict):
    raw_input: dict
    purity_check: bool
    thermal_profile: dict
    is_compliant: bool

def validate_quality(state: CoalProcessingState):
    purity = state['raw_input'].get('carbon_purity', 0)
    return {'purity_check': purity >= 85.0}

def analyze_thermal_profile(state: CoalProcessingState):
    # Simulate thermal analysis for coking coal
    return {'thermal_profile': {'calorific': 7000, 'moisture': 0.05}, 'is_compliant': state['purity_check']}

graph = StateGraph(CoalProcessingState)
graph.add_node('validate', validate_quality)
graph.add_node('thermal', analyze_thermal_profile)
graph.add_edge('validate', 'thermal')
graph.add_edge('thermal', END)
graph.set_entry_point('validate')
graph = graph.compile()
