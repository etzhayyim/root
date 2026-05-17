from typing import TypedDict
from langgraph.graph import StateGraph, END

class ProcurementState(TypedDict):
    drug_name: str
    compliance_ok: bool
    temp_log: list

def validate_license(state: ProcurementState):
    state['compliance_ok'] = True
    return 'check_temp'

def check_temp(state: ProcurementState):
    return 'FINISH'

graph = StateGraph(ProcurementState)
graph.add_node('validate_license', validate_license)
graph.add_node('check_temp', check_temp)
graph.add_edge('validate_license', 'check_temp')
graph.add_edge('check_temp', END)
graph.set_entry_point('validate_license')
graph = graph.compile()