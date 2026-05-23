from typing import TypedDict, List
from langgraph.graph import StateGraph, END

class CementPostState(TypedDict):
    spec_data: dict
    validation_results: List[str]
    approved: bool

def validate_specs(state: CementPostState):
    results = []
    if state['spec_data'].get('compression', 0) < 30:
        results.append('Compression strength below threshold')
    return {'validation_results': results, 'approved': len(results) == 0}

def finalize_order(state: CementPostState):
    return {'approved': True}

graph = StateGraph(CementPostState)
graph.add_node('validate', validate_specs)
graph.add_node('finalize', finalize_order)
graph.add_edge('validate', 'finalize')
graph.set_entry_point('validate')
graph.set_finish_point('finalize')
graph.compile()
