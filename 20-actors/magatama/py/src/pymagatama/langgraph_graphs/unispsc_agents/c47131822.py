from typing import TypedDict
from langgraph.graph import StateGraph, END

class CarbonCleanerState(TypedDict):
    material_safety_data: str
    compliance_status: bool
    hazard_classification: str

def validate_compliance(state: CarbonCleanerState):
    is_compliant = 'SDS' in state['material_safety_data']
    return {'compliance_status': is_compliant}

def check_hazards(state: CarbonCleanerState):
    severity = 'High' if 'flammable' in state['hazard_classification'] else 'Medium'
    return {'hazard_classification': severity}

graph = StateGraph(CarbonCleanerState)
graph.add_node('validate', validate_compliance)
graph.add_node('hazards', check_hazards)
graph.set_entry_point('validate')
graph.add_edge('validate', 'hazards')
graph.add_edge('hazards', END)
graph = graph.compile()
