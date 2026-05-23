from typing import TypedDict
from langgraph.graph import StateGraph, END

class WaterProcurementState(TypedDict):
    ph: float
    purity_level: str
    is_compliant: bool

def validate_water_quality(state: WaterProcurementState):
    # Simulate quality inspection logic
    is_compliant = 6.5 <= state['ph'] <= 8.5 and state['purity_level'] == 'potable'
    return {'is_compliant': is_compliant}

def route_by_compliance(state: WaterProcurementState):
    return 'compliant' if state['is_compliant'] else 'reject'

graph = StateGraph(WaterProcurementState)
graph.add_node('validate', validate_water_quality)
graph.add_edge('validate', END)
graph.set_entry_point('validate')
compiled_graph = graph.compile()
