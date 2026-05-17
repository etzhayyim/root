from langgraph.graph import StateGraph, END
from typing import TypedDict
class MicroscopeLightState(TypedDict):
    spec_data: dict
    validated: bool
def validate_optics(state: MicroscopeLightState):
    light_type = state['spec_data'].get('type')
    return {'validated': light_type in ['LED', 'Halogen']}
def check_compliance(state: MicroscopeLightState):
    return {'validated': state['validated'] and state['spec_data'].get('power_certified', False)}
graph = StateGraph(MicroscopeLightState)
graph.add_node('validate', validate_optics)
graph.add_node('compliance', check_compliance)
graph.set_entry_point('validate')
graph.add_edge('validate', 'compliance')
graph.add_edge('compliance', END)
graph = graph.compile()