from typing import TypedDict
from langgraph.graph import StateGraph, END

class VacuumMoldState(TypedDict):
    part_specs: dict
    validation_passed: bool

def validate_specs(state: VacuumMoldState):
    # Perform dimensional and heat-resistance validation
    thickness = state['part_specs'].get('thickness', 0)
    state['validation_passed'] = thickness > 0
    return state

workflow = StateGraph(VacuumMoldState)
workflow.add_node('validate', validate_specs)
workflow.set_entry_point('validate')
workflow.add_edge('validate', END)
graph = workflow.compile()
