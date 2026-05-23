from typing import TypedDict
from langgraph.graph import StateGraph, END

class LeatherState(TypedDict):
    material_spec: dict
    compliance_report: str

def validate_leather_quality(state: LeatherState):
    spec = state['material_spec']
    if spec.get('thickness_mm', 0) < 0.5:
        return {'compliance_report': 'REJECTED: Thickness below threshold'}
    return {'compliance_report': 'APPROVED: Quality standards met'}

def update_inventory(state: LeatherState):
    return {'compliance_report': state['compliance_report'] + ' | Inventory Updated'}

graph = StateGraph(LeatherState)
graph.add_node('validate', validate_leather_quality)
graph.add_node('inventory', update_inventory)
graph.set_entry_point('validate')
graph.add_edge('validate', 'inventory')
graph.add_edge('inventory', END)
graph = graph.compile()
