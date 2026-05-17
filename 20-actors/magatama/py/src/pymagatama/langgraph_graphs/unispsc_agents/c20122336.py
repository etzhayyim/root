from typing import TypedDict, Annotated, List
from langgraph.graph import StateGraph, END

class ActuatorState(TypedDict):
    spec_data: dict
    validation_results: List[str]
    is_compliant: bool

def validate_specs(state: ActuatorState) -> ActuatorState:
    specs = state['spec_data']
    results = []
    if specs.get('rated_torque_nm', 0) <= 0:
        results.append('Invalid torque value')
    return {'validation_results': results, 'is_compliant': len(results) == 0}

def route_by_compliance(state: ActuatorState) -> str:
    return 'process' if state['is_compliant'] else 'flag_error'

graph = StateGraph(ActuatorState)
graph.add_node('validate', validate_specs)
graph.add_node('process', lambda s: s)
graph.add_node('flag_error', lambda s: s)
graph.set_entry_point('validate')
graph.add_conditional_edges('validate', route_by_compliance)
graph.add_edge('process', END)
graph.add_edge('flag_error', END)
app = graph.compile()