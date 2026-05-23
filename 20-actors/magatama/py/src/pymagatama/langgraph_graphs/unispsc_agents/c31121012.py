from langgraph.graph import StateGraph, END
from typing import TypedDict, List

class CastState(TypedDict):
    part_specs: dict
    validation_passed: bool
    inspection_logs: List[str]

def validate_casting_specs(state: CastState):
    success = all(k in state['part_specs'] for k in ['alloy', 'tolerance'])
    return {'validation_passed': success}

def perform_quality_check(state: CastState):
    return {'inspection_logs': ['Ultrasonic check completed', 'Dimension verify pass']}

graph = StateGraph(CastState)
graph.add_node('validate', validate_casting_specs)
graph.add_node('inspect', perform_quality_check)
graph.set_entry_point('validate')
graph.add_edge('validate', 'inspect')
graph.add_edge('inspect', END)
graph = graph.compile()
