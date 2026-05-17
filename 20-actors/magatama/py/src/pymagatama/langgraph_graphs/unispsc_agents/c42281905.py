from langgraph.graph import StateGraph, END
from typing import TypedDict, List

class SealerState(TypedDict):
    specs: dict
    validation_results: List[str]
    is_compliant: bool

def validate_specs(state: SealerState):
    results = []
    if state['specs'].get('ISO_11607_compliance'):
        results.append('ISO 11607 compliant')
    else:
        results.append('CRITICAL: Missing ISO 11607 compliance')
    return {'validation_results': results, 'is_compliant': 'CRITICAL' not in str(results)}

def finalize_procurement(state: SealerState):
    return {'validation_results': state['validation_results'] + ['Procurement ready']}

graph = StateGraph(SealerState)
graph.add_node('validate', validate_specs)
graph.add_node('finalize', finalize_procurement)
graph.add_edge('validate', 'finalize')
graph.add_edge('finalize', END)
graph.set_entry_point('validate')
graph = graph.compile()