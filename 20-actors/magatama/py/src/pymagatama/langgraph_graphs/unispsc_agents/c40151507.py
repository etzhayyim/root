from typing import TypedDict
from langgraph.graph import StateGraph, END

class PumpState(TypedDict):
    spec_data: dict
    validation_result: bool

def validate_efficiency(state: PumpState):
    power = state['spec_data'].get('power', 0)
    flow = state['spec_data'].get('flow', 0)
    return {'validation_result': flow / power > 0.5 if power > 0 else False}

def route_by_type(state: PumpState):
    return 'process_submersible' if state['spec_data'].get('type') == 'sub' else 'process_surface'

graph = StateGraph(PumpState)
graph.add_node('validate', validate_efficiency)
graph.add_node('process_submersible', lambda x: x)
graph.add_node('process_surface', lambda x: x)
graph.set_entry_point('validate')
graph.add_conditional_edges('validate', route_by_type)
graph.add_edge('process_submersible', END)
graph.add_edge('process_surface', END)

graph = graph.compile()
