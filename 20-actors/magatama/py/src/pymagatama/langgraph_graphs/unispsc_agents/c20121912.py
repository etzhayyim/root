from typing import TypedDict, Annotated
from langgraph.graph import StateGraph, END

class PumpState(TypedDict):
    pressure_req: float
    flow_rate: float
    validation_passed: bool
    compliance_tags: list[str]

def validate_specs(state: PumpState) -> PumpState:
    state['validation_passed'] = state['pressure_req'] > 0 and state['flow_rate'] > 0
    return state

def check_compliance(state: PumpState) -> PumpState:
    if state['validation_passed']:
        state['compliance_tags'].append('ISO_HYDRAULIC_COMPLIANT')
    return state

graph = StateGraph(PumpState)
graph.add_node('validate', validate_specs)
graph.add_node('compliance', check_compliance)
graph.set_entry_point('validate')
graph.add_edge('validate', 'compliance')
graph.add_edge('compliance', END)
graph = graph.compile()