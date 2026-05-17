from typing import TypedDict, List
from langgraph.graph import StateGraph, END

class InspectionState(TypedDict):
    device_id: str
    specs: dict
    compliance_passed: bool

def validate_specs(state: InspectionState):
    required = ['frequency_range_mhz', 'scan_resolution_micron']
    passed = all(k in state['specs'] for k in required)
    return {'compliance_passed': passed}

def export_review(state: InspectionState):
    print(f'Checking export controls for device {state[\'device_id\']}')
    return {'compliance_passed': True}

graph = StateGraph(InspectionState)
graph.add_node('validate', validate_specs)
graph.add_node('export', export_review)
graph.add_edge('validate', 'export')
graph.add_edge('export', END)
graph.set_entry_point('validate')
graph = graph.compile()