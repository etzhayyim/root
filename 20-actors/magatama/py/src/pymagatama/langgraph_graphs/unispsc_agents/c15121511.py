from typing import TypedDict, Annotated, Sequence
import operator
from langgraph.graph import StateGraph, END

class CarbonFiberState(TypedDict):
    spec_data: dict
    validation_results: Annotated[list[str], operator.add]
    is_compliant: bool

def validate_spec(state: CarbonFiberState):
    spec = state['spec_data']
    results = []
    if spec.get('tensile_strength_mpa', 0) < 3500:
        results.append('Tensile strength below threshold')
    return {'validation_results': results}

def compliance_check(state: CarbonFiberState):
    is_compliant = len(state['validation_results']) == 0
    return {'is_compliant': is_compliant}

graph = StateGraph(CarbonFiberState)
graph.add_node('validate', validate_spec)
graph.add_node('compliance', compliance_check)
graph.add_edge('validate', 'compliance')
graph.add_edge('compliance', END)
graph.set_entry_point('validate')
graph = graph.compile()
