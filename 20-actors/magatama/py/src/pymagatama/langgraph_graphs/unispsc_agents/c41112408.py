from typing import TypedDict
from langgraph.graph import StateGraph, END

class IntensifierState(TypedDict):
    pressure_rating: float
    material_spec: str
    validation_passed: bool

def validate_pressure_specs(state: IntensifierState):
    if state['pressure_rating'] > 1000:
        return {'validation_passed': True}
    return {'validation_passed': False}

def perform_safety_check(state: IntensifierState):
    print(f'Checking integrity for {state['material_spec']}')
    return {'validation_passed': state['validation_passed'] and True}

workflow = StateGraph(IntensifierState)
workflow.add_node('validate', validate_pressure_specs)
workflow.add_node('safety', perform_safety_check)
workflow.add_edge('validate', 'safety')
workflow.add_edge('safety', END)
workflow.set_entry_point('validate')
graph = workflow.compile()
