from typing import TypedDict, Annotated, List
from langgraph.graph import StateGraph, END

class AerospaceMaterialState(TypedDict):
    material_spec: dict
    validation_passed: bool
    inspection_results: List[str]

def validate_material_grade(state: AerospaceMaterialState):
    grade = state['material_spec'].get('grade')
    is_valid = grade in ['AMS4911', 'AMS4928']
    return {'validation_passed': is_valid, 'inspection_results': ['Grade checked']}

def perform_ultrasonic_test(state: AerospaceMaterialState):
    return {'inspection_results': state['inspection_results'] + ['Ultrasonic scan completed']}

graph = StateGraph(AerospaceMaterialState)
graph.add_node('validate_grade', validate_material_grade)
graph.add_node('ultrasonic_test', perform_ultrasonic_test)
graph.set_entry_point('validate_grade')
graph.add_edge('validate_grade', 'ultrasonic_test')
graph.add_edge('ultrasonic_test', END)
app = graph.compile()
