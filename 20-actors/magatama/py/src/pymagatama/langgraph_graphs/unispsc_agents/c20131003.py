from typing import TypedDict, Annotated, List
from langgraph.graph import StateGraph, END
import operator

class NozzleState(TypedDict):
    spec: dict
    validation_results: Annotated[List[str], operator.add]
    is_compliant: bool

def validate_nozzle_specs(state: NozzleState):
    spec = state['spec']
    results = []
    if spec.get('orifice_diameter_mm', 0) <= 0:
        results.append('Invalid orifice diameter')
    if spec.get('pressure_rating_bar', 0) < 0:
        results.append('Negative pressure rating')
    return {'validation_results': results}

def check_compliance(state: NozzleState):
    return {'is_compliant': len(state['validation_results']) == 0}

graph = StateGraph(NozzleState)
graph.add_node('validate', validate_nozzle_specs)
graph.add_node('compliance', check_compliance)
graph.set_entry_point('validate')
graph.add_edge('validate', 'compliance')
graph.add_edge('compliance', END)

graph = graph.compile()