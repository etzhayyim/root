from typing import TypedDict
from langgraph.graph import StateGraph, END

class ProcessingState(TypedDict):
    batch_id: str
    is_compliant: bool
    lab_report: dict

def validate_quality(state: ProcessingState):
    # Business logic for concentrate validation
    brix = state['lab_report'].get('brix', 0)
    state['is_compliant'] = brix >= 60
    return state

def route_by_compliance(state: ProcessingState):
    return 'process' if state['is_compliant'] else 'reject'

graph = StateGraph(ProcessingState)
graph.add_node('validate', validate_quality)
graph.add_edge('validate', 'process')
graph.set_entry_point('validate')
graph.set_finish_point('process')
graph = graph.compile()