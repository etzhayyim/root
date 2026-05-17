from typing import TypedDict
from langgraph.graph import StateGraph, END

class TesterState(TypedDict):
    model_id: str
    calibration_status: bool
    validation_score: float

def validate_specs(state: TesterState):
    state['validation_score'] = 1.0 if state['calibration_status'] else 0.0
    return state

def check_compliance(state: TesterState):
    return 'compliant' if state['validation_score'] >= 1.0 else 'non-compliant'

graph = StateGraph(TesterState)
graph.add_node('validate', validate_specs)
graph.set_entry_point('validate')
graph.add_edge('validate', END)
graph = graph.compile()