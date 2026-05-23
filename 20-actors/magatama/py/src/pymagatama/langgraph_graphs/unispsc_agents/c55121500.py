from typing import TypedDict
from langgraph.graph import StateGraph, END

class TagState(TypedDict):
    spec_data: dict
    validation_log: list
    is_compliant: bool

def validate_material(state: TagState):
    log = state.get('validation_log', [])
    material = state['spec_data'].get('material_type')
    log.append(f'Validating material specifications: {material}')
    return {'validation_log': log}

def check_compliance(state: TagState):
    compliance = state['spec_data'].get('material_type') is not None
    return {'is_compliant': compliance}

graph = StateGraph(TagState)
graph.add_node('validate', validate_material)
graph.add_node('compliance', check_compliance)
graph.add_edge('validate', 'compliance')
graph.add_edge('compliance', END)
graph.set_entry_point('validate')
app = graph.compile()
