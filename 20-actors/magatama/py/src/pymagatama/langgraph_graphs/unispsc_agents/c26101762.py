from typing import TypedDict
from langgraph.graph import StateGraph, END

class EngineComponentState(TypedDict):
    specs: dict
    validation_Passed: bool
    compliance_Score: float

def validate_material(state: EngineComponentState):
    # Simulate material compliance check for metallurgical specs
    state['validation_Passed'] = state['specs'].get('tensile_strength', 0) > 500
    return state

def check_tolerances(state: EngineComponentState):
    # Simulate geometric tolerance check
    state['compliance_Score'] = 0.95 if state['validation_Passed'] else 0.0
    return state

graph = StateGraph(EngineComponentState)
graph.add_node('validate', validate_material)
graph.add_node('tolerances', check_tolerances)
graph.set_entry_point('validate')
graph.add_edge('validate', 'tolerances')
graph.add_edge('tolerances', END)
graph = graph.compile()