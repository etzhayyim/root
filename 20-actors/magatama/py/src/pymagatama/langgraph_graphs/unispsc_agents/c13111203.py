from typing import TypedDict, Annotated, List
from langgraph.graph import StateGraph, END

class LubricantState(TypedDict):
    commodity_code: str
    spec_data: dict
    validation_checks: List[str]
    is_approved: bool

def validate_viscosity(state: LubricantState) -> LubricantState:
    if 'viscosity_grade' in state['spec_data']:
        state['validation_checks'].append('Viscosity valid')
    return state

def check_compliance(state: LubricantState) -> LubricantState:
    if 'iso_standard_compliance' in state['spec_data']:
        state['validation_checks'].append('ISO compliant')
        state['is_approved'] = True
    return state

graph = StateGraph(LubricantState)
graph.add_node('validate_viscosity', validate_viscosity)
graph.add_node('check_compliance', check_compliance)
graph.add_edge('validate_viscosity', 'check_compliance')
graph.add_edge('check_compliance', END)
graph.set_entry_point('validate_viscosity')
graph = graph.compile()