from typing import TypedDict
from langgraph.graph import StateGraph, END

class FlameDetectorState(TypedDict):
    spec_data: dict
    validation_passed: bool
    error_log: list

def validate_specs(state: FlameDetectorState):
    required = ['response_time', 'temp_limit']
    passed = all(k in state['spec_data'] for k in required)
    return {'validation_passed': passed}

workflow = StateGraph(FlameDetectorState)
workflow.add_node('validate', validate_specs)
workflow.set_entry_point('validate')
workflow.add_edge('validate', END)
graph = workflow.compile()
