from typing import TypedDict
from langgraph.graph import StateGraph, END

class SurgicalLightState(TypedDict):
    model_number: str
    illuminance_lux: int
    compliance_docs: list[str]
    approved: bool

def validate_specs(state: SurgicalLightState):
    is_valid = state['illuminance_lux'] >= 40000 and 'ISO_13485' in state['compliance_docs']
    return {'approved': is_valid}

graph = StateGraph(SurgicalLightState)
graph.add_node('validate', validate_specs)
graph.set_entry_point('validate')
graph.add_edge('validate', END)
graph = graph.compile()