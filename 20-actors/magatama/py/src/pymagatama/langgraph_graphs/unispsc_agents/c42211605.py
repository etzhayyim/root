from typing import TypedDict
from langgraph.graph import StateGraph, END

class BathPillowState(TypedDict):
    spec_data: dict
    approved: bool
    compliance_report: str

def validate_safety_specs(state: BathPillowState):
    material = state['spec_data'].get('material')
    is_safe = material in ['polyurethane', 'silicone']
    return {'approved': is_safe, 'compliance_report': 'Safety check pass' if is_safe else 'Material non-compliant'}

def routing_logic(state: BathPillowState):
    return 'approved' if state['approved'] else END

graph = StateGraph(BathPillowState)
graph.add_node('validate', validate_safety_specs)
graph.set_entry_point('validate')
graph.add_edge('validate', END)
graph = graph.compile()