from typing import TypedDict, List
from langgraph.graph import StateGraph, END

class GearState(TypedDict):
    spec: dict
    validation_results: List[str]
    is_compliant: bool

def validate_gear_specs(state: GearState):
    errors = []
    if state['spec'].get('module', 0) <= 0:
        errors.append('Invalid module size')
    return {'validation_results': errors, 'is_compliant': len(errors) == 0}

def check_material_cert(state: GearState):
    return {'validation_results': state['validation_results'] + ['Material cert verified']}

graph = StateGraph(GearState)
graph.add_node('validate', validate_gear_specs)
graph.add_node('check_cert', check_material_cert)
graph.set_entry_point('validate')
graph.add_edge('validate', 'check_cert')
graph.add_edge('check_cert', END)
graph = graph.compile()
