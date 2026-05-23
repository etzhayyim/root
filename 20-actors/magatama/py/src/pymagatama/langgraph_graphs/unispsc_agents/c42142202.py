from typing import TypedDict, Annotated, Sequence
import operator
from langgraph.graph import StateGraph, END

class HydrotherapyState(TypedDict):
    spec_data: dict
    validation_results: Annotated[Sequence[str], operator.add]
    is_compliant: bool

def validate_medical_standards(state: HydrotherapyState):
    checks = []
    if 'ISO 13485' not in state['spec_data'].get('certs', []):
        checks.append('Missing ISO 13485')
    return {'validation_results': checks}

def safety_compliance_check(state: HydrotherapyState):
    is_compliant = len(state['validation_results']) == 0
    return {'is_compliant': is_compliant}

graph = StateGraph(HydrotherapyState)
graph.add_node('validate', validate_medical_standards)
graph.add_node('safety', safety_compliance_check)
graph.set_entry_point('validate')
graph.add_edge('validate', 'safety')
graph.add_edge('safety', END)
graph = graph.compile()
