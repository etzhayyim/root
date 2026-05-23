from typing import TypedDict
from langgraph.graph import StateGraph, END

class DentalFurnitureState(TypedDict):
    spec_data: dict
    validation_passed: bool
    compliance_report: str

def validate_furniture_specs(state: DentalFurnitureState):
    specs = state['spec_data']
    passed = 'ISO_13485_certification' in specs and specs['upholstery_antimicrobial_rating'] > 95
    return {"validation_passed": passed, "compliance_report": "Validated against medical standards" if passed else "Compliance failure"}

def route_by_validation(state: DentalFurnitureState):
    return "process" if state['validation_passed'] else END

graph = StateGraph(DentalFurnitureState)
graph.add_node("validate", validate_furniture_specs)
graph.add_node("process", lambda x: {"compliance_report": "Ready for clinical installation"})
graph.set_entry_point("validate")
graph.add_conditional_edges("validate", route_by_validation)
graph.add_edge("process", END)
graph = graph.compile()
