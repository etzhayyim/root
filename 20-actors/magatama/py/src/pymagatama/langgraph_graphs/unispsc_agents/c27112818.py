from typing import TypedDict, List
from langgraph.graph import StateGraph, END

class ViseState(TypedDict):
    jaw_width: float
    material_type: str
    is_compatible: bool
    validation_logger: List[str]

def validate_specs(state: ViseState):
    log = []
    comp = state['jaw_width'] > 0 and state['material_type'] in ['Aluminum', 'Nylon', 'Copper']
    log.append(f'Validation result: {comp}')
    return {'is_compatible': comp, 'validation_logger': log}

graph = StateGraph(ViseState)
graph.add_node('validate', validate_specs)
graph.set_entry_point('validate')
graph.add_edge('validate', END)
graph = graph.compile()