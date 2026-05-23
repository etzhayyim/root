from typing import TypedDict, Annotated, Sequence
from langgraph.graph import StateGraph, END
import operator

class LoadBalancerState(TypedDict):
    requirements: dict
    validation_results: Annotated[Sequence[str], operator.add]
    is_compliant: bool

def validate_specs(state: LoadBalancerState):
    results = []
    if state['requirements'].get('throughput_gbps', 0) < 10:
        results.append('Insufficient throughput')
    if not state['requirements'].get('redundancy_configuration'):
        results.append('Missing redundancy config')
    return {'validation_results': results, 'is_compliant': len(results) == 0}

def route_procurement(state: LoadBalancerState):
    return 'compliant' if state['is_compliant'] else 'reject'

graph = StateGraph(LoadBalancerState)
graph.add_node('validate', validate_specs)
graph.add_edge('validate', END)
graph.set_entry_point('validate')
