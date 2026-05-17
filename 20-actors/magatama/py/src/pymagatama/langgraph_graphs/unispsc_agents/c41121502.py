from typing import TypedDict
from langgraph.graph import StateGraph, END

class DiluterState(TypedDict):
    accuracy_check: bool
    calibration_data: dict
    approved: bool

def validate_specs(state: DiluterState):
    acc = state.get('calibration_data', {}).get('accuracy', 0)
    return {'accuracy_check': acc > 99.0}

def decision_node(state: DiluterState):
    return 'approved' if state['accuracy_check'] else END

builder = StateGraph(DiluterState)
builder.add_node('validate', validate_specs)
builder.add_node('final', lambda x: {'approved': True})
builder.set_entry_point('validate')
builder.add_conditional_edges('validate', decision_node, {'approved': 'final'})
builder.add_edge('final', END)
graph = builder.compile()