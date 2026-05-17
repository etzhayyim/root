from typing import TypedDict
from langgraph.graph import StateGraph, END

class XRayFilterState(TypedDict):
    filter_spec: dict
    validation_status: str

def validate_specs(state: XRayFilterState):
    required = ['material_purity', 'attenuation_coefficient']
    if all(k in state['filter_spec'] for k in required):
        return {'validation_status': 'COMPLIANT'}
    return {'validation_status': 'REJECTED'}

def safety_check(state: XRayFilterState):
    if state['validation_status'] == 'COMPLIANT':
        return {'validation_status': 'SAFETY_VERIFIED'}
    return {'validation_status': 'FAILED'}

graph = StateGraph(XRayFilterState)
graph.add_node('validate', validate_specs)
graph.add_node('safety', safety_check)
graph.add_edge('validate', 'safety')
graph.add_edge('safety', END)
graph.set_entry_point('validate')
app = graph.compile()