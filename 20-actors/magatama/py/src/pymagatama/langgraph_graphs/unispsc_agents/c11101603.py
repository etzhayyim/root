from typing import TypedDict, Annotated, Sequence
import operator
from langgraph.graph import StateGraph, END

class CarbonFiberState(TypedDict):
    spec_requirements: dict
    validation_results: Annotated[Sequence[str], operator.add]
    is_compliant: bool

def validate_tensile_strength(state: CarbonFiberState):
    strength = state['spec_requirements'].get('tensile_strength_mpa', 0)
    if strength >= 3500:
        return {'validation_results': ['Tensile strength meets aerospace grade'], 'is_compliant': True}
    return {'validation_results': ['Tensile strength insufficient'], 'is_compliant': False}

def verify_certification(state: CarbonFiberState):
    certs = state['spec_requirements'].get('certification_standard', [])
    if 'AS9100' in certs:
        return {'validation_results': ['Certification verified']}
    return {'validation_results': ['Certification missing']}

graph = StateGraph(CarbonFiberState)
graph.add_node('validate_strength', validate_tensile_strength)
graph.add_node('verify_certs', verify_certification)
graph.set_entry_point('validate_strength')
graph.add_edge('validate_strength', 'verify_certs')
graph.add_edge('verify_certs', END)
graph = graph.compile()
