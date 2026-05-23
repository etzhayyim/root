from typing import TypedDict, Annotated, List
from langgraph.graph import StateGraph, END

class ProcurementState(TypedDict):
    commodity_code: str
    spec_data: dict
    validation_passed: bool
    errors: List[str]

def validate_gmp_compliance(state: ProcurementState) -> ProcurementState:
    if 'GMP_certificate_version' not in state['spec_data']:
        state['errors'].append('Missing GMP certification')
        state['validation_passed'] = False
    return state

def check_purity_threshold(state: ProcurementState) -> ProcurementState:
    if state.get('validation_passed', True):
        purity = state['spec_data'].get('batch_purity_percentage', 0)
        if purity < 99.0:
            state['errors'].append('Purity below 99.0% threshold')
            state['validation_passed'] = False
    return state

graph = StateGraph(ProcurementState)
graph.add_node('validate_gmp', validate_gmp_compliance)
graph.add_node('check_purity', check_purity_threshold)
graph.add_edge('validate_gmp', 'check_purity')
graph.add_edge('check_purity', END)
graph.set_entry_point('validate_gmp')
graph = graph.compile()
