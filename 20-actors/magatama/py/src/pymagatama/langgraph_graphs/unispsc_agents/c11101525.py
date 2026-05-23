from typing import TypedDict, Annotated, Sequence
import operator
from langgraph.graph import StateGraph, END

class CarbonFiberState(TypedDict):
    material_id: str
    spec_requirements: dict
    validation_results: Annotated[Sequence[str], operator.add]
    is_approved: bool

def validate_tensile_strength(state: CarbonFiberState):
    strength = state['spec_requirements'].get('tensile_strength_mpa', 0)
    if strength >= 3500:
        return {'validation_results': ['Tensile strength meets aerospace grade']}
    return {'validation_results': ['Tensile strength below aerospace requirements']}

def check_certification(state: CarbonFiberState):
    certs = state['spec_requirements'].get('certs', [])
    if 'AS9100' in certs:
        return {'is_approved': True}
    return {'is_approved': False}

graph = StateGraph(CarbonFiberState)
graph.add_node('validate_physics', validate_tensile_strength)
graph.add_node('check_compliance', check_certification)
graph.add_edge('validate_physics', 'check_compliance')
graph.add_edge('check_compliance', END)
graph.set_entry_point('validate_physics')
graph = graph.compile()
