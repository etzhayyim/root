from typing import TypedDict, Annotated, Sequence
import operator
from langgraph.graph import StateGraph, END

class AdhesionState(TypedDict):
    material_spec: dict
    validation_results: Annotated[Sequence[str], operator.add]
    status: str

def validate_material(state: AdhesionState):
    spec = state['material_spec']
    results = []
    if spec.get('viscosity_cps', 0) < 100:
        results.append('CRITICAL_LOW_VISCOSITY')
    if spec.get('tensile_strength_mpa', 0) < 5:
        results.append('INSUFFICIENT_BOND_STRENGTH')
    return {'validation_results': results}

def process_workflow(state: AdhesionState):
    if 'CRITICAL_LOW_VISCOSITY' in state['validation_results']:
        return {'status': 'REJECTED_SAFETY_FAILURE'}
    return {'status': 'READY_FOR_ASSEMBLY'}

graph = StateGraph(AdhesionState)
graph.add_node('validate', validate_material)
graph.add_node('process', process_workflow)
graph.set_entry_point('validate')
graph.add_edge('validate', 'process')
graph.add_edge('process', END)
compile_graph = graph.compile()