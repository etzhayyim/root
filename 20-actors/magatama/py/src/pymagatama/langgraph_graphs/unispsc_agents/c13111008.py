from typing import TypedDict, Annotated, List
from langgraph.graph import StateGraph, END
import operator

class MetalProcurementState(TypedDict):
    material_spec: dict
    validation_results: Annotated[List[str], operator.add]
    is_approved: bool

def validate_composition(state: MetalProcurementState):
    spec = state['material_spec']
    if 'alloy_composition_percent' in spec and spec['alloy_composition_percent'] > 99.0:
        return {'validation_results': ['Composition high purity verified'], 'is_approved': True}
    return {'validation_results': ['Composition check failed'], 'is_approved': False}

def check_compliance(state: MetalProcurementState):
    if state.get('is_approved'):
        return {'validation_results': ['Compliance standards met']}
    return {'validation_results': ['Compliance verification pending']}

graph = StateGraph(MetalProcurementState)
graph.add_node('validate', validate_composition)
graph.add_node('compliance', check_compliance)
graph.set_entry_point('validate')
graph.add_edge('validate', 'compliance')
graph.add_edge('compliance', END)
graph = graph.compile()
