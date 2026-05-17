from typing import TypedDict
from langgraph.graph import StateGraph, END

class SludgeTruckState(TypedDict):
    requirements: dict
    validation_status: bool
    compliance_report: str

def validate_specs(state: SludgeTruckState):
    required_keys = ['tank_capacity', 'pump_rating', 'emission_standard']
    all_present = all(k in state['requirements'] for k in required_keys)
    return {'validation_status': all_present, 'compliance_report': 'Validated' if all_present else 'Missing key data'}

def approval_check(state: SludgeTruckState):
    return 'Approved' if state['validation_status'] else 'Rejected'

graph = StateGraph(SludgeTruckState)
graph.add_node('validate', validate_specs)
graph.add_node('approval', approval_check)
graph.add_edge('validate', 'approval')
graph.add_edge('approval', END)
graph.set_entry_point('validate')
graph = graph.compile()