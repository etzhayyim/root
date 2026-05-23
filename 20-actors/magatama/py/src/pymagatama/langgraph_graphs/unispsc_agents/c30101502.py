from typing import TypedDict
from langgraph.graph import StateGraph, END

class AlloyProcurementState(TypedDict):
    material_spec: dict
    compliance_check: bool
    validation_log: list

def validate_material(state: AlloyProcurementState):
    grade = state['material_spec'].get('grade')
    is_compliant = grade is not None and len(grade) > 0
    return {'compliance_check': is_compliant, 'validation_log': ['Material grade checked']}

def approve_order(state: AlloyProcurementState):
    print('Proceeding to order fulfillment for alloy angles')
    return {'validation_log': state['validation_log'] + ['Order approved']}

graph = StateGraph(AlloyProcurementState)
graph.add_node('validate', validate_material)
graph.add_node('approve', approve_order)
graph.set_entry_point('validate')
graph.add_edge('validate', 'approve')
graph.add_edge('approve', END)
graph = graph.compile()
