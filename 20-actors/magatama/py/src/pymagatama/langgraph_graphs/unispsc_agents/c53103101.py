from typing import TypedDict, List
from langgraph.graph import StateGraph, END

class WaistcoatState(TypedDict):
    spec_data: dict
    validation_errors: List[str]
    is_compliant: bool

def validate_material(state: WaistcoatState):
    errors = []
    if 'material' not in state['spec_data']:
        errors.append('Material composition missing.')
    return {'validation_errors': errors}

def final_check(state: WaistcoatState):
    return {'is_compliant': len(state['validation_errors']) == 0}

graph = StateGraph(WaistcoatState)
graph.add_node('validate', validate_material)
graph.add_node('check', final_check)
graph.set_entry_point('validate')
graph.add_edge('validate', 'check')
graph.add_edge('check', END)
graph = graph.compile()
