from typing import TypedDict, Annotated, List
from langgraph.graph import StateGraph, END

class FlowMeterState(TypedDict):
    commodity_id: str
    flow_range: float
    compatibility_list: List[str]
    validation_score: float

def validate_specs(state: FlowMeterState) -> FlowMeterState:
    # Simulate spec validation logic for flow meter compliance
    state['validation_score'] = 1.0 if state['flow_range'] > 0 else 0.0
    return state

def check_compliance(state: FlowMeterState) -> str:
    return 'VALID' if state['validation_score'] == 1.0 else 'INVALID'

graph = StateGraph(FlowMeterState)
graph.add_node('validate', validate_specs)
graph.add_edge('validate', END)
graph.set_entry_point('validate')
graph = graph.compile()