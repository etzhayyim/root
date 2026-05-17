from typing import TypedDict
from langgraph.graph import StateGraph, END

class WaterDryerState(TypedDict):
    spec_data: dict
    validation_status: bool

def validate_specs(state: WaterDryerState):
    required = ['capacity', 'pressure', 'dew_point']
    valid = all(k in state['spec_data'] for k in required)
    return {'validation_status': valid}

def route_verification(state: WaterDryerState):
    return 'validate' if state.get('spec_data') else END

graph = StateGraph(WaterDryerState)
graph.add_node('validate', validate_specs)
graph.set_entry_point('validate')
graph.add_edge('validate', END)
graph = graph.compile()