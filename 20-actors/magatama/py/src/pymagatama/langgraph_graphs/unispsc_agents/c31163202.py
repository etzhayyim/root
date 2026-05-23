from typing import TypedDict
from langgraph.graph import StateGraph, END

class RetainingRingState(TypedDict):
    specs: dict
    validation_status: bool
    error_log: list

def validate_specs(state: RetainingRingState):
    required = ['material', 'dimension', 'standard']
    missing = [f for f in required if f not in state['specs']]
    return {'validation_status': len(missing) == 0, 'error_log': missing}

def route_by_validation(state: RetainingRingState):
    return 'process' if state['validation_status'] else END

graph = StateGraph(RetainingRingState)
graph.add_node('validate', validate_specs)
graph.add_node('process', lambda x: x)
graph.set_entry_point('validate')
graph.add_conditional_edges('validate', route_by_validation)
graph.add_edge('process', END)
graph = graph.compile()
