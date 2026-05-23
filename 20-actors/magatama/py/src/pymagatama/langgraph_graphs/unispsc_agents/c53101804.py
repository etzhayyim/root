from typing import TypedDict
from langgraph.graph import StateGraph, END

class GarmentState(TypedDict):
    spec_data: dict
    validation_passed: bool
    inspection_report: str

def validate_materials(state: GarmentState):
    composition = state['spec_data'].get('fabric_composition', '')
    return {'validation_passed': len(composition) > 0}

def generate_report(state: GarmentState):
    return {'inspection_report': 'Quality check complete for women\'s outerwear.'}

graph = StateGraph(GarmentState)
graph.add_node('validate', validate_materials)
graph.add_node('report', generate_report)
graph.set_entry_point('validate')
graph.add_edge('validate', 'report')
graph.add_edge('report', END)
graph = graph.compile()
