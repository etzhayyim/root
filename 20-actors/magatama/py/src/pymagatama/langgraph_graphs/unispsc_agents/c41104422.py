from typing import TypedDict, List
from langgraph.graph import StateGraph, END

class IncubatorState(TypedDict):
    spec_config: dict
    validation_results: List[str]
    is_compliant: bool

def validate_specs(state: IncubatorState):
    config = state['spec_config']
    results = []
    if config.get('temp_stability', 0) > 0.5:
        results.append('Temperature instability detected')
    return {'validation_results': results, 'is_compliant': len(results) == 0}

def approval_step(state: IncubatorState):
    return {'is_compliant': state.get('is_compliant', False)}

graph = StateGraph(IncubatorState)
graph.add_node('validate', validate_specs)
graph.add_node('approve', approval_step)
graph.add_edge('validate', 'approve')
graph.add_edge('approve', END)
graph.set_entry_point('validate')
graph = graph.compile()