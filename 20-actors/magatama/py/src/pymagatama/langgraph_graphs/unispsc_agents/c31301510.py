from typing import TypedDict, List
from langgraph.graph import StateGraph, END

class ForgingState(TypedDict):
    specs: dict
    validation_passed: bool
    compliance_risk: str

def validate_materials(state: ForgingState):
    grade = state['specs'].get('grade')
    state['validation_passed'] = grade in ['304', '316L', '17-4PH']
    return state

def check_export_control(state: ForgingState):
    state['compliance_risk'] = 'high' if state['specs'].get('aerospace_grade') else 'standard'
    return state

graph = StateGraph(ForgingState)
graph.add_node('material_check', validate_materials)
graph.add_node('export_check', check_export_control)
graph.set_entry_point('material_check')
graph.add_edge('material_check', 'export_check')
graph.add_edge('export_check', END)
app = graph.compile()