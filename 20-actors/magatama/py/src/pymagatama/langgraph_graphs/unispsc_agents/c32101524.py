from typing import TypedDict
from langgraph.graph import StateGraph, END

class PhaseShifterState(TypedDict):
    spec_data: dict
    validated: bool
    export_control_flag: bool

def validate_specs(state: PhaseShifterState):
    specs = state['spec_data']
    valid = all(k in specs for k in ['frequency', 'loss'])
    return {'validated': valid}

def check_compliance(state: PhaseShifterState):
    is_restricted = state['spec_data'].get('frequency', 0) > 40
    return {'export_control_flag': is_restricted}

graph = StateGraph(PhaseShifterState)
graph.add_node('validate', validate_specs)
graph.add_node('compliance', check_compliance)
graph.set_entry_point('validate')
graph.add_edge('validate', 'compliance')
graph.add_edge('compliance', END)
graph = graph.compile()
