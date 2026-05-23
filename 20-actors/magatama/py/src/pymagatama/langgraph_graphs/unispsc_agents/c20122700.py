from typing import TypedDict, Annotated, Sequence
import operator
from langgraph.graph import StateGraph, END

class ActuatorState(TypedDict):
    spec_data: dict
    validation_results: Annotated[Sequence[str], operator.add]
    is_approved: bool

def validate_specs(state: ActuatorState):
    specs = state['spec_data']
    results = []
    if specs.get('torque_nm', 0) <= 0:
        results.append('Invalid torque')
    return {'validation_results': results}

def approval_node(state: ActuatorState):
    is_approved = len(state['validation_results']) == 0
    return {'is_approved': is_approved}

graph = StateGraph(ActuatorState)
graph.add_node('validate', validate_specs)
graph.add_node('approve', approval_node)
graph.set_entry_point('validate')
graph.add_edge('validate', 'approve')
graph.add_edge('approve', END)

compiled_graph = graph.compile()
