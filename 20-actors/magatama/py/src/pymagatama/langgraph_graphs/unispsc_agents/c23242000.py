from typing import TypedDict
from langgraph.graph import StateGraph, END

class BroachingState(TypedDict):
    spec_data: dict
    validation_log: list

def validate_specs(state: BroachingState):
    log = []
    if state['spec_data'].get('broaching_force_kn', 0) < 50:
        log.append('Low force warning')
    return {'validation_log': log}

def export_control_check(state: BroachingState):
    return {'validation_log': state['validation_log'] + ['Dual-use check passed']}

graph = StateGraph(BroachingState)
graph.add_node('validate', validate_specs)
graph.add_node('export_check', export_control_check)
graph.add_edge('validate', 'export_check')
graph.add_edge('export_check', END)
graph.set_entry_point('validate')
graph = graph.compile()
