from typing import TypedDict, List
from langgraph.graph import StateGraph, END

class BottleState(TypedDict):
    bottle_type: str
    material: str
    validation_passed: bool
    compliance_report: str

def validate_materials(state: BottleState):
    # logic to check chemical resilience
    return {'validation_passed': True if state['material'] in ['HDPE', 'LDPE'] else False}

def generate_compliance(state: BottleState):
    return {'compliance_report': 'Passed regulatory safety inspection' if state['validation_passed'] else 'Failed'}

graph = StateGraph(BottleState)
graph.add_node('validation', validate_materials)
graph.add_node('compliance', generate_compliance)
graph.set_entry_point('validation')
graph.add_edge('validation', 'compliance')
graph.add_edge('compliance', END)
graph = graph.compile()