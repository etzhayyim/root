from typing import TypedDict, Annotated, List
from langgraph.graph import StateGraph, END

class AbrasiveState(TypedDict):
    material_spec: dict
    validation_results: List[str]
    is_compliant: bool

def validate_abrasive_specs(state: AbrasiveState):
    spec = state['material_spec']
    results = []
    if spec.get('hardness_mohs', 0) < 6:
        results.append('Hardness below minimum threshold')
    return {'validation_results': results, 'is_compliant': len(results) == 0}

def route_to_procurement(state: AbrasiveState):
    return 'compliant' if state['is_compliant'] else 'reject'

graph = StateGraph(AbrasiveState)
graph.add_node('validate', validate_abrasive_specs)
graph.add_edge('validate', END)
graph.set_entry_point('validate')