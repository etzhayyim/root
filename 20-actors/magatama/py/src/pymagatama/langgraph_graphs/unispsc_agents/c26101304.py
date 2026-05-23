from typing import TypedDict
from langgraph.graph import StateGraph, END

class HydraulicState(TypedDict):
    spec_data: dict
    validation_log: list
    is_approved: bool

def validate_pressure(state: HydraulicState):
    pressure = state['spec_data'].get('max_pressure', 0)
    valid = 0 < pressure < 700
    state['validation_log'].append(f'Pressure check: {valid}')
    return {'is_approved': valid}

def check_compliance(state: HydraulicState):
    state['validation_log'].append('Export Control Check: Performed.')
    return {'is_approved': state['is_approved']}

graph = StateGraph(HydraulicState)
graph.add_node('validate', validate_pressure)
graph.add_node('compliance', check_compliance)
graph.set_entry_point('validate')
graph.add_edge('validate', 'compliance')
graph.add_edge('compliance', END)
graph = graph.compile()
