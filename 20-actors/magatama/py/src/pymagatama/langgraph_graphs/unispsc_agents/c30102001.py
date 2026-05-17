from langgraph.graph import StateGraph, END
from typing import TypedDict, List

class AlloyState(TypedDict):
    material_data: dict
    validation_passed: bool
    compliance_flags: List[str]

def validate_material_specs(state: AlloyState):
    fields = ['grade', 'thickness', 'tensile_strength']
    passed = all(k in state['material_data'] for k in fields)
    return {**state, 'validation_passed': passed}

def check_compliance(state: AlloyState):
    flags = ['dual-use-check'] if state['material_data'].get('is_strategic') else []
    return {**state, 'compliance_flags': flags}

graph = StateGraph(AlloyState)
graph.add_node('validate', validate_material_specs)
graph.add_node('compliance', check_compliance)
graph.add_edge('validate', 'compliance')
graph.add_edge('compliance', END)
graph.set_entry_point('validate')
graph = graph.compile()