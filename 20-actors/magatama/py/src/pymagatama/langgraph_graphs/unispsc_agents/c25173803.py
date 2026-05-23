from typing import TypedDict
from langgraph.graph import StateGraph, END

class AxleState(TypedDict):
    spec_data: dict
    validation_results: list
    is_approved: bool

def validate_materials(state: AxleState):
    check = state['spec_data'].get('tensile_strength', 0) >= 400
    return {'validation_results': [f'Material strength valid: {check}'], 'is_approved': check}

def structural_check(state: AxleState):
    return {'validation_results': state['validation_results'] + ['Structural integrity confirmed']}

graph = StateGraph(AxleState)
graph.add_node('material_check', validate_materials)
graph.add_node('structural_check', structural_check)
graph.set_entry_point('material_check')
graph.add_edge('material_check', 'structural_check')
graph.add_edge('structural_check', END)

graph = graph.compile()
