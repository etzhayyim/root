from typing import TypedDict
from langgraph.graph import StateGraph, END

class DentalLightState(TypedDict):
    spec_data: dict
    is_compliant: bool

def validate_illumination(state: DentalLightState):
    light_data = state['spec_data']
    compliant = light_data.get('lux', 0) >= 20000 and light_data.get('cri', 0) >= 90
    return {'is_compliant': compliant}

def route_by_compliance(state: DentalLightState):
    return 'process' if state['is_compliant'] else END

graph = StateGraph(DentalLightState)
graph.add_node('validate', validate_illumination)
graph.add_node('process', lambda x: x)
graph.set_entry_point('validate')
graph.add_conditional_edges('validate', route_by_compliance)
graph.add_edge('process', END)
graph = graph.compile()
