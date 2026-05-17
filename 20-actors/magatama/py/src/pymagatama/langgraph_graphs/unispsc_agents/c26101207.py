from typing import TypedDict
from langgraph.graph import StateGraph, END

class MotorState(TypedDict):
    specs: dict
    validation_score: float
    is_compliant: bool

def validate_specs(state: MotorState):
    # Business logic for industrial motor specs
    state['is_compliant'] = state['specs'].get('force', 0) > 0
    return state

def check_export_control(state: MotorState):
    # Logic for dual-use export compliance check
    state['validation_score'] = 1.0 if state['is_compliant'] else 0.0
    return state

graph = StateGraph(MotorState)
graph.add_node('validate', validate_specs)
graph.add_node('export_review', check_export_control)
graph.set_entry_point('validate')
graph.add_edge('validate', 'export_review')
graph.add_edge('export_review', END)
graph = graph.compile()