from typing import TypedDict
from langgraph.graph import StateGraph, END

class TesterState(TypedDict):
    spec_data: dict
    validation_passed: bool
    error_log: list

def validate_specs(state: TesterState):
    required = ['safety_rating', 'calibration_date']
    passed = all(k in state['spec_data'] for k in required)
    return {'validation_passed': passed}

graph = StateGraph(TesterState)
graph.add_node('validate', validate_specs)
graph.set_entry_point('validate')
graph.add_edge('validate', END)
graph = graph.compile()
