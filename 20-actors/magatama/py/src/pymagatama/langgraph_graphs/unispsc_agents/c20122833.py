from typing import TypedDict, Annotated, List
from langgraph.graph import StateGraph, END

class BearingState(TypedDict):
    spec: dict
    validation_results: List[str]
    approved: bool

def validate_specs(state: BearingState):
    spec = state['spec']
    results = []
    if 'ISO_tolerance_grade' not in spec:
        results.append('Missing ISO_tolerance_grade')
    return {'validation_results': results, 'approved': len(results) == 0}

def route_by_validation(state: BearingState):
    return 'process' if state['approved'] else END

def process_bearing_logistics(state: BearingState):
    return {'validation_results': state['validation_results'] + ['Logistics confirmed']}

graph = StateGraph(BearingState)
graph.add_node('validate', validate_specs)
graph.add_node('process', process_bearing_logistics)
graph.set_entry_point('validate')
graph.add_conditional_edges('validate', route_by_validation)
graph.add_edge('process', END)

graph = graph.compile()