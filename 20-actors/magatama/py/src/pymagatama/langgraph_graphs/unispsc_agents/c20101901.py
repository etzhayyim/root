from typing import TypedDict, Annotated
from langgraph.graph import StateGraph, END

class DrillBitState(TypedDict):
    spec_id: str
    material_certified: bool
    hardness_score: float
    inspection_passed: bool

def validate_material(state: DrillBitState) -> DrillBitState:
    # Simulate material property validation logic
    state['material_certified'] = True
    return state

def run_stress_test(state: DrillBitState) -> DrillBitState:
    # Simulate stress testing protocol
    state['inspection_passed'] = state['hardness_score'] > 60.0
    return state

graph = StateGraph(DrillBitState)
graph.add_node('validate', validate_material)
graph.add_node('stress_test', run_stress_test)
graph.set_entry_point('validate')
graph.add_edge('validate', 'stress_test')
graph.add_edge('stress_test', END)

compiled_graph = graph.compile()
