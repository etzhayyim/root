from typing import TypedDict
from langgraph.graph import StateGraph, END

class DentalFiberState(TypedDict):
    spec_data: dict
    validation_log: list

def validate_optical_specs(state: DentalFiberState):
    specs = state['spec_data']
    logs = []
    if specs.get('intensity') < 500: logs.append('Error: Insufficient light output')
    return {'validation_log': logs}

def autoclave_check(state: DentalFiberState):
    if state.get('spec_data', {}).get('autoclavable', False):
        return {'validation_log': state['validation_log'] + ['Thermal resistance confirmed']}
    return {'validation_log': state['validation_log'] + ['Warning: Non-autoclavable component']}

graph = StateGraph(DentalFiberState)
graph.add_node('validate_optical', validate_optical_specs)
graph.add_node('check_hygiene', autoclave_check)
graph.set_entry_point('validate_optical')
graph.add_edge('validate_optical', 'check_hygiene')
graph.add_edge('check_hygiene', END)
graph = graph.compile()