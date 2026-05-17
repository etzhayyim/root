from typing import TypedDict, Annotated, Sequence
from langgraph.graph import StateGraph, END

class AlloyState(TypedDict):
    alloy_code: str
    material_specs: dict
    validation_passed: bool
    inspection_log: list

def validate_material_grade(state: AlloyState):
    # Simulate metallurgical validation logic
    grade = state['material_specs'].get('alloy_grade', '')
    is_valid = grade.startswith('70') or grade.startswith('20')
    return {'validation_passed': is_valid}

def perform_inspection(state: AlloyState):
    log = state.get('inspection_log', [])
    log.append('Ultrasonic testing and spectrographic analysis completed.')
    return {'inspection_log': log}

graph = StateGraph(AlloyState)
graph.add_node('validate', validate_material_grade)
graph.add_node('inspect', perform_inspection)
graph.set_entry_point('validate')
graph.add_edge('validate', 'inspect')
graph.add_edge('inspect', END)
graph = graph.compile()