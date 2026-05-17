from typing import TypedDict
from langgraph.graph import StateGraph, END

class PumpProcurementState(TypedDict):
    flow_rate: float
    head_pressure: float
    validation_status: bool

def validate_specs(state: PumpProcurementState):
    state['validation_status'] = state['flow_rate'] > 0 and state['head_pressure'] > 0
    return 'validated' if state['validation_status'] else 'error'

graph = StateGraph(PumpProcurementState)
graph.add_node('validate', validate_specs)
graph.set_entry_point('validate')
graph.add_edge('validate', END)
graph = graph.compile()