from typing import TypedDict, List
from langgraph.graph import StateGraph, END

class SteelAssemblyState(TypedDict):
    specs: dict
    validation_passed: bool
    compliance_report: str

def validate_material_grade(state: SteelAssemblyState):
    grade = state['specs'].get('grade')
    return {'validation_passed': grade is not None}

def perform_weld_check(state: SteelAssemblyState):
    return {'compliance_report': 'Weld inspection completed'}

graph = StateGraph(SteelAssemblyState)
graph.add_node('val_material', validate_material_grade)
graph.add_node('check_weld', perform_weld_check)
graph.add_edge('val_material', 'check_weld')
graph.add_edge('check_weld', END)
graph.set_entry_point('val_material')
compiled_graph = graph.compile()
