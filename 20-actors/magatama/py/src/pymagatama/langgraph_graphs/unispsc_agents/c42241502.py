from langgraph.graph import StateGraph, END
from typing import TypedDict

class CastPaddingState(TypedDict):
    spec_data: dict
    validation_results: list
    is_compliant: bool

def validate_biocompatibility(state: CastPaddingState):
    results = state.get('validation_results', [])
    cert = state['spec_data'].get('iso_10993_compliance')
    results.append('Validated ISO 10993' if cert else 'Missing ISO 10993')
    return {'validation_results': results}

def check_compliance(state: CastPaddingState):
    is_compliant = all('Validated' in r for r in state['validation_results'])
    return {'is_compliant': is_compliant}

graph = StateGraph(CastPaddingState)
graph.add_node('validate', validate_biocompatibility)
graph.add_node('compliance', check_compliance)
graph.set_entry_point('validate')
graph.add_edge('validate', 'compliance')
graph.add_edge('compliance', END)
