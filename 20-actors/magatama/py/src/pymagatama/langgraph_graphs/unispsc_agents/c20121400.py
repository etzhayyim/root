from typing import TypedDict, Annotated
from langgraph.graph import StateGraph, END
from langgraph.graph.message import add_messages

class BearingState(TypedDict):
    part_number: str
    spec_data: dict
    validation_score: float
    inspection_status: str

def validate_bearing_specs(state: BearingState) -> BearingState:
    # Logic to validate bearing tolerances and material specs
    state['validation_score'] = 1.0 if 'load_capacity' in state['spec_data'] else 0.0
    return state

def run_load_test_simulation(state: BearingState) -> BearingState:
    # Simulate stress test logic
    state['inspection_status'] = 'PASSED' if state['validation_score'] > 0.5 else 'FAILED'
    return state

graph = StateGraph(BearingState)
graph.add_node('validate', validate_bearing_specs)
graph.add_node('test', run_load_test_simulation)
graph.add_edge('validate', 'test')
graph.add_edge('test', END)
graph.set_entry_point('validate')
graph = graph.compile()
