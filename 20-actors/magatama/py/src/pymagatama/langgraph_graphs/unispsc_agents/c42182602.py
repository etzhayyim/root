from langgraph.graph import StateGraph, END
from typing import TypedDict

class MedicalLightState(TypedDict):
    spec_data: dict
    validation_passed: bool

def validate_lux(state: MedicalLightState):
    lux = state['spec_data'].get('illuminance_lux', 0)
    return {'validation_passed': lux >= 40000}

def finalize_procurement(state: MedicalLightState):
    return state

graph = StateGraph(MedicalLightState)
graph.add_node('validate', validate_lux)
graph.add_node('finalize', finalize_procurement)
graph.set_entry_point('validate')
graph.add_edge('validate', 'finalize')
graph.add_edge('finalize', END)
graph = graph.compile()