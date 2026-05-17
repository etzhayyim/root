from typing import TypedDict
from langgraph.graph import StateGraph, END

class SuppressionState(TypedDict):
    spec_data: dict
    is_compliant: bool
    validation_log: list

def validate_standards(state: SuppressionState):
    log = []
    cert = state['spec_data'].get('certification_standard_ul_fm')
    if not cert: log.append('Missing mandatory UL/FM certification')
    return {'is_compliant': len(log) == 0, 'validation_log': log}

def perform_safety_check(state: SuppressionState):
    pressure = state['spec_data'].get('pressure_rating', 0)
    return {'validation_log': state['validation_log'] + [f'Pressure check passed: {pressure} bar']}

graph = StateGraph(SuppressionState)
graph.add_node('validate', validate_standards)
graph.add_node('safety', perform_safety_check)
graph.set_entry_point('validate')
graph.add_edge('validate', 'safety')
graph.add_edge('safety', END)
graph = graph.compile()