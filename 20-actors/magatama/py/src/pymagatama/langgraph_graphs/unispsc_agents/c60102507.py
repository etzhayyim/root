from typing import TypedDict
from langgraph.graph import StateGraph, END

class TapeProcurementState(TypedDict):
    width: float
    length: float
    is_compatible: bool
    validation_status: str

def validate_specs(state: TapeProcurementState):
    if state['width'] > 0 and state['length'] > 0:
        return {'validation_status': 'PASSED'}
    return {'validation_status': 'FAILED'}

def check_compatibility(state: TapeProcurementState):
    return {'is_compatible': True}

graph = StateGraph(TapeProcurementState)
graph.add_node('validate', validate_specs)
graph.add_node('compatibility', check_compatibility)
graph.set_entry_point('validate')
graph.add_edge('validate', 'compatibility')
graph.add_edge('compatibility', END)
graph = graph.compile()
