from typing import TypedDict
from langgraph.graph import StateGraph, END

class GardenState(TypedDict):
    project_id: str
    spec_doc: str
    validation_passed: bool

def validate_specs(state: GardenState):
    # Business logic for garden specifications validation
    passed = 'irrigation_plan' in state['spec_doc'] and 'soil_analysis' in state['spec_doc']
    return {'validation_passed': passed}

def approve_project(state: GardenState):
    return {'validation_passed': True}

graph = StateGraph(GardenState)
graph.add_node('validate', validate_specs)
graph.add_node('approve', approve_project)
graph.set_entry_point('validate')
graph.add_edge('validate', 'approve')
graph.add_edge('approve', END)
graph = graph.compile()
