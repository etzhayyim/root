from typing import TypedDict
from langgraph.graph import StateGraph, END

class ProcedureTableState(TypedDict):
    specs: dict
    is_compliant: bool

def validate_medical_standards(state: ProcedureTableState):
    device_class = state['specs'].get('class', 'Class II')
    is_compliant = device_class in ['Class II', 'Class III']
    return {'is_compliant': is_compliant}

def route_by_compliance(state: ProcedureTableState):
    return 'compliant' if state['is_compliant'] else 'flag_for_review'

graph = StateGraph(ProcedureTableState)
graph.add_node('validate', validate_medical_standards)
graph.set_entry_point('validate')
graph.add_conditional_edges('validate', route_by_compliance, {'compliant': END, 'flag_for_review': END})
graph.compile()
