from typing import TypedDict, List
from langgraph.graph import StateGraph, END

class CountermeasureState(TypedDict):
    specs: dict
    compliance_validated: bool
    export_license_granted: bool
    final_approval: bool

def validate_tech_specs(state: CountermeasureState):
    # Simulate CAD/Military spec validation logic
    state['compliance_validated'] = all(k in state['specs'] for k in ['MIL-SPEC', 'range'])
    print('Specs Validated')
    return state

def check_export_controls(state: CountermeasureState):
    # Business logic for restricted goods export lookup
    state['export_license_granted'] = True
    return state

graph = StateGraph(CountermeasureState)
graph.add_node('validate_specs', validate_tech_specs)
graph.add_node('check_export', check_export_controls)
graph.set_entry_point('validate_specs')
graph.add_edge('validate_specs', 'check_export')
graph.add_edge('check_export', END)
graph = graph.compile()
