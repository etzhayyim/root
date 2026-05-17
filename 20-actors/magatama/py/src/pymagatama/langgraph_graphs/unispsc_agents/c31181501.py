from typing import TypedDict
from langgraph.graph import StateGraph, END

class GasketState(TypedDict):
    spec_data: dict
    validation_result: bool
    error_log: list

def validate_material(state: GasketState):
    material = state['spec_data'].get('material')
    is_valid = material in ['PTFE', 'Nylon', 'PVC', 'Polyethylene']
    return {'validation_result': is_valid, 'error_log': [] if is_valid else ['Invalid material type']}

def check_dimensions(state: GasketState):
    if state['validation_result']:
        dim = state['spec_data'].get('thickness', 0)
        state['validation_result'] = dim > 0
    return state

graph = StateGraph(GasketState)
graph.add_node('validate_material', validate_material)
graph.add_node('check_dimensions', check_dimensions)
graph.set_entry_point('validate_material')
graph.add_edge('validate_material', 'check_dimensions')
graph.add_edge('check_dimensions', END)
graph = graph.compile()