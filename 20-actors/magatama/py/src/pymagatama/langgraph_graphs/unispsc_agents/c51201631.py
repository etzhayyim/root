from typing import TypedDict
from langgraph.graph import StateGraph, END

class VaccineProcurementState(TypedDict):
    temp_log: float
    qc_passed: bool
    compliance_checked: bool

def validate_cold_chain(state: VaccineProcurementState):
    state['qc_passed'] = 2.0 <= state['temp_log'] <= 8.0
    return state

def check_compliance(state: VaccineProcurementState):
    state['compliance_checked'] = True
    return state

graph = StateGraph(VaccineProcurementState)
graph.add_node('validate', validate_cold_chain)
graph.add_node('compliance', check_compliance)
graph.set_entry_point('validate')
graph.add_edge('validate', 'compliance')
graph.add_edge('compliance', END)
graph = graph.compile()