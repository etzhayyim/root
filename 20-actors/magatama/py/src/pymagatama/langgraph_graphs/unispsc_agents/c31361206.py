from typing import TypedDict
from langgraph.graph import StateGraph, END

class AssemblyState(TypedDict):
    spec_data: dict
    validation_log: list
    is_compliant: bool

def validate_material(state: AssemblyState):
    material = state['spec_data'].get('material')
    is_valid = material in ['FRP', 'Nylon', 'Composite']
    return {'validation_log': [f'Material check: {is_valid}'], 'is_compliant': is_valid}

def structural_integrity_check(state: AssemblyState):
    load_capacity = state['spec_data'].get('load_capacity', 0)
    status = load_capacity > 0
    return {'validation_log': state['validation_log'] + [f'Load test: {status}']}

graph = StateGraph(AssemblyState)
graph.add_node('validate_material', validate_material)
graph.add_node('structural_integrity', structural_integrity_check)
graph.set_entry_point('validate_material')
graph.add_edge('validate_material', 'structural_integrity')
graph.add_edge('structural_integrity', END)
graph = graph.compile()