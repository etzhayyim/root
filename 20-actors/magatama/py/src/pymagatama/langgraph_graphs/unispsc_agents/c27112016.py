from langgraph.graph import StateGraph, END
from typing import TypedDict, List

class HedgeClippersState(TypedDict):
    item_id: str
    specs: dict
    validated: bool
    compliance_report: str

def validate_specs(state: HedgeClippersState):
    valid = 'blade_material' in state['specs'] and 'cutting_capacity_mm' in state['specs']
    return {'validated': valid, 'compliance_report': 'Specs verified' if valid else 'Missing required fields'}

def approve_procurement(state: HedgeClippersState):
    return {'compliance_report': 'Ready for purchase order generation'}

graph = StateGraph(HedgeClippersState)
graph.add_node('validate', validate_specs)
graph.add_node('approve', approve_procurement)
graph.set_entry_point('validate')
graph.add_edge('validate', 'approve')
graph.add_edge('approve', END)
graph = graph.compile()