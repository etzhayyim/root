from typing import TypedDict
from langgraph.graph import StateGraph, END

class State(TypedDict):
    specification: dict
    validation_result: bool
    error_log: list

def validate_iso_compliance(state: State):
    is_compliant = state['specification'].get('iso_11140_cert') is True
    return {'validation_result': is_compliant, 'error_log': [] if is_compliant else ['Missing ISO certification']}

def check_shelf_life(state: State):
    if not state.get('validation_result'): return state
    valid = state['specification'].get('days_to_expiry', 0) > 90
    return {'validation_result': valid, 'error_log': [] if valid else ['Insufficient shelf life']}

graph = StateGraph(State)
graph.add_node('iso_check', validate_iso_compliance)
graph.add_node('expiry_check', check_shelf_life)
graph.add_edge('iso_check', 'expiry_check')
graph.add_edge('expiry_check', END)
graph.set_entry_point('iso_check')
app = graph.compile()
