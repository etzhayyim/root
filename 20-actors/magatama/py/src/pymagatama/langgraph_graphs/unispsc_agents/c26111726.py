from typing import TypedDict, List
from langgraph.graph import StateGraph, END

class BatterySpecState(TypedDict):
    spec_fields: dict
    validation_passed: bool
    compliance_warnings: List[str]

def validate_battery_specs(state: BatterySpecState):
    fields = state['spec_fields']
    warnings = []
    if 'voltage_rating' not in fields: warnings.append('Missing voltage rating')
    if 'safety_certification_standard' not in fields: warnings.append('Missing safety cert')
    state['validation_passed'] = len(warnings) == 0
    state['compliance_warnings'] = warnings
    return state

graph = StateGraph(BatterySpecState)
graph.add_node('validate', validate_battery_specs)
graph.set_entry_point('validate')
graph.add_edge('validate', END)
graph = graph.compile()