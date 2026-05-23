from typing import TypedDict
from langgraph.graph import StateGraph, END

class TripodState(TypedDict):
    specifications: dict
    validation_result: bool
    error_log: list

def validate_load_capacity(state: TripodState):
    capacity = state['specifications'].get('load_capacity', 0)
    valid = capacity > 0
    return {'validation_result': valid, 'error_log': [] if valid else ['Invalid load capacity']}

def finalize_order(state: TripodState):
    return {'error_log': state['error_log'] + ['Procurement approved']}

graph = StateGraph(TripodState)
graph.add_node('validate', validate_load_capacity)
graph.add_node('finalize', finalize_order)
graph.add_edge('validate', 'finalize')
graph.add_edge('finalize', END)
graph.set_entry_point('validate')
