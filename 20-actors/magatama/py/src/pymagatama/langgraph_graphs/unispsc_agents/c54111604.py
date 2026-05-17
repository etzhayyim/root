from typing import TypedDict, List
from langgraph.graph import StateGraph, END

class HourglassState(TypedDict):
    spec_details: dict
    validation_passed: bool
    errors: List[str]

def validate_materials(state: HourglassState):
    glass_type = state['spec_details'].get('material', '')
    return {'validation_passed': glass_type in ['Borosilicate', 'Tempered'], 'errors': [] if glass_type else ['Invalid Material']}

def check_accuracy(state: HourglassState):
    tolerance = state['spec_details'].get('tolerance', 0.0)
    passed = tolerance < 0.05
    return {'validation_passed': state['validation_passed'] and passed}

workflow = StateGraph(HourglassState)
workflow.add_node('validate', validate_materials)
workflow.add_node('accuracy', check_accuracy)
workflow.set_entry_point('validate')
workflow.add_edge('validate', 'accuracy')
workflow.add_edge('accuracy', END)
graph = workflow.compile()