from typing import TypedDict
from langgraph.graph import StateGraph, END

class WaterConditionerState(TypedDict):
    chemical_data: dict
    compliance_check: bool
    approved: bool

def validate_compliance(state: WaterConditionerState):
    is_compliant = state['chemical_data'].get('safety_sheet_provided', False)
    return {'compliance_check': is_compliant}

def final_approval(state: WaterConditionerState):
    return {'approved': state['compliance_check']}

graph = StateGraph(WaterConditionerState)
graph.add_node('validate', validate_compliance)
graph.add_node('approve', final_approval)
graph.set_entry_point('validate')
graph.add_edge('validate', 'approve')
graph.add_edge('approve', END)

compiled_graph = graph.compile()
