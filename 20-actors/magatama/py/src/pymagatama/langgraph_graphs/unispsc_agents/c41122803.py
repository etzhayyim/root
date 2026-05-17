from typing import TypedDict, List
from langgraph.graph import StateGraph, END

class SedimentationState(TypedDict):
    rack_specs: dict
    validation_passed: bool
    error_log: List[str]

def validate_material(state: SedimentationState):
    material = state['rack_specs'].get('material')
    valid_materials = ['polypropylene', 'polycarbonate', 'stainless_steel']
    if material in valid_materials:
        return {'validation_passed': True}
    return {'validation_passed': False, 'error_log': ['Invalid material type']}

workflow = StateGraph(SedimentationState)
workflow.add_node('validate_material', validate_material)
workflow.set_entry_point('validate_material')
workflow.add_edge('validate_material', END)
graph = workflow.compile()