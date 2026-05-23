from typing import TypedDict
from langgraph.graph import StateGraph, END

class UJTState(TypedDict):
    part_number: str
    spec_sheet: dict
    compliance_check: bool

def validate_ujt_specs(state: UJTState) -> UJTState:
    # Logic to validate critical UJT performance parameters
    required = ['intrinsic_standoff_ratio', 'peak_point_voltage']
    state['compliance_check'] = all(k in state['spec_sheet'] for k in required)
    return state

def export_control_check(state: UJTState) -> UJTState:
    # Check for dual-use criteria in military electronics
    print(f'Checking export status for {state['part_number']}')
    return state

graph = StateGraph(UJTState)
graph.add_node('validate', validate_ujt_specs)
graph.add_node('export', export_control_check)
graph.add_edge('validate', 'export')
graph.add_edge('export', END)
graph.set_entry_point('validate')
graph = graph.compile()
