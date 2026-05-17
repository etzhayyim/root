from typing import TypedDict
from langgraph.graph import StateGraph, END

class TractorProcurementState(TypedDict):
    engine_power: float
    emission_compliant: bool
    approved: bool

def validate_specs(state: TractorProcurementState):
    state['approved'] = state['engine_power'] > 50 and state['emission_compliant']
    return state

graph = StateGraph(TractorProcurementState)
graph.add_node('validate', validate_specs)
graph.set_entry_point('validate')
graph.add_edge('validate', END)
graph = graph.compile()