from typing import TypedDict, List
from langgraph.graph import StateGraph, END

class ProcurementState(TypedDict):
    juice_specs: dict
    validation_passed: bool
    error_logs: List[str]

def validate_quality(state: ProcurementState):
    specs = state['juice_specs']
    passed = specs.get('brix', 0) > 10 and 'certification' in specs
    return {'validation_passed': passed}

def route_procurement(state: ProcurementState):
    return 'validate' if state['juice_specs'] else END

graph = StateGraph(ProcurementState)
graph.add_node('validate', validate_quality)
graph.set_entry_point('validate')
graph.add_edge('validate', END)
graph = graph.compile()