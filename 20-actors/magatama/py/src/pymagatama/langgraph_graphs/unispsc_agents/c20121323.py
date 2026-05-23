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
    if 'torque' not in specs or specs['torque'] <= 0:
        results.append('INVALID_TORQUE')
    if 'voltage' not in specs:
        results.append('MISSING_VOLTAGE')
    return {'validation_results': results}

def approval_check(state: ActuatorState):
    if len(state['validation_results']) == 0:
        return {'is_approved': True}
    return {'is_approved': False}

graph = StateGraph(ActuatorState)
graph.add_node('validate', validate_specs)
graph.add_node('approve', approval_check)
graph.add_edge('validate', 'approve')
graph.add_edge('approve', END)
graph.set_entry_point('validate')
graph = graph.compile()
