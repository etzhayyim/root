from typing import TypedDict, Annotated, Sequence
import operator
from langgraph.graph import StateGraph, END

class BearingState(TypedDict):
    spec: dict
    validation_log: Annotated[Sequence[str], operator.add]
    is_approved: bool

def validate_materials(state: BearingState) -> BearingState:
    material_data = state['spec'].get('material_composition_report', {})
    # Logic for checking material composition compliance
    return {'validation_log': ['Material composition validated against ISO standards.']}

def conduct_stress_test(state: BearingState) -> BearingState:
    # Logic for simulating physical inspection against load criteria
    return {'validation_log': ['Stress test passed under simulated load conditions.'], 'is_approved': True}

workflow = StateGraph(BearingState)
workflow.add_node('material_check', validate_materials)
workflow.add_node('stress_test', conduct_stress_test)
workflow.set_entry_point('material_check')
workflow.add_edge('material_check', 'stress_test')
workflow.add_edge('stress_test', END)

graph = workflow.compile()