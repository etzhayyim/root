from typing import TypedDict
from langgraph.graph import StateGraph, END

class ThermalBatchState(TypedDict):
    temp_range: str
    stability: float
    compliance: bool
    approved: bool

def validate_specs(state: ThermalBatchState):
    # Validate thermostatic bath specifications
    is_stable = state['stability'] <= 0.5
    return {'approved': is_stable and state['compliance']}

graph = StateGraph(ThermalBatchState)
graph.add_node('validate', validate_specs)
graph.set_entry_point('validate')
graph.add_edge('validate', END)
graph = graph.compile()
