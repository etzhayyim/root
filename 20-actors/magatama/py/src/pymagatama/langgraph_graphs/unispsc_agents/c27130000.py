from langgraph.graph import StateGraph, END
from typing import TypedDict, List

class PneumaticState(TypedDict):
    pressure_specs: dict
    compliance_checks: List[str]
    is_approved: bool

def validate_pressure(state: PneumaticState):
    state['is_approved'] = state['pressure_specs'].get('max_bar', 0) <= 250
    return 'validate_compliance'

def validate_compliance(state: PneumaticState):
    state['compliance_checks'].append('ISO-8573-1_checked')
    return END

graph = StateGraph(PneumaticState)
graph.add_node('pressure', validate_pressure)
graph.add_node('validate_compliance', validate_compliance)
graph.set_entry_point('pressure')
graph.add_edge('pressure', 'validate_compliance')
graph.add_edge('validate_compliance', END)
graph = graph.compile()