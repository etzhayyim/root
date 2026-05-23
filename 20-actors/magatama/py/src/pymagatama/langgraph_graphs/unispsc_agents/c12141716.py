from typing import TypedDict, Annotated, Sequence
import operator
from langgraph.graph import StateGraph, END

class ElastomerState(TypedDict):
    spec_requirements: dict
    validation_results: Annotated[Sequence[str], operator.add]
    is_compliant: bool

def validate_thermal_specs(state: ElastomerState):
    temp_rating = state['spec_requirements'].get('Thermal_Stability_Rating', 0)
    if temp_rating > 200:
        return {'validation_results': ['Thermal spec validated at >200C'], 'is_compliant': True}
    return {'validation_results': ['Thermal spec below standard'], 'is_compliant': False}

def structural_check(state: ElastomerState):
    if state['is_compliant']:
        return {'validation_results': ['Structural integrity check passed']}
    return {'validation_results': ['Structural integrity check failed']}

graph = StateGraph(ElastomerState)
graph.add_node('thermal_validation', validate_thermal_specs)
graph.add_node('structural_integrity', structural_check)
graph.set_entry_point('thermal_validation')
graph.add_edge('thermal_validation', 'structural_integrity')
graph.add_edge('structural_integrity', END)
graph = graph.compile()
