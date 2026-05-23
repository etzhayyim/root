from langgraph.graph import StateGraph, END
from typing import TypedDict, List
class BiopsyUnitState(TypedDict):
    device_id: str
    compliance_passed: bool
    validation_logs: List[str]
def validate_medical_compliance(state: BiopsyUnitState):
    state['validation_logs'].append('Checking ISO 13485 standards...')
    state['compliance_passed'] = True
    return state
def check_vacuum_specs(state: BiopsyUnitState):
    state['validation_logs'].append('Verifying vacuum pressure calibration...')
    return state
workflow = StateGraph(BiopsyUnitState)
workflow.add_node('compliance', validate_medical_compliance)
workflow.add_node('vacuum_check', check_vacuum_specs)
workflow.set_entry_point('compliance')
workflow.add_edge('compliance', 'vacuum_check')
workflow.add_edge('vacuum_check', END)
graph = workflow.compile()
