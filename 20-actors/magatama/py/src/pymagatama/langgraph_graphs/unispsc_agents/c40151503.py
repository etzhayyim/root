from typing import TypedDict
from langgraph.graph import StateGraph, END

class PumpState(TypedDict):
    specs: dict
    approved: bool
    validation_log: list

def validate_specs(state: PumpState):
    log = []
    if state['specs'].get('flow_rate', 0) <= 0:
        log.append('Invalid Flow Rate')
    return {'validation_log': log}

def decision_node(state: PumpState):
    return 'approved' if not state['validation_log'] else 'rejected'

graph = StateGraph(PumpState)
graph.add_node('validate', validate_specs)
graph.set_entry_point('validate')
graph.add_edge('validate', END)
graph.compile()
