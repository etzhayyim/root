from typing import TypedDict, Annotated, Sequence
import operator
from langgraph.graph import StateGraph, END

class ActuatorState(TypedDict):
    spec_data: dict
    validation_log: Annotated[Sequence[str], operator.add]
    is_compliant: bool

def validate_specs(state: ActuatorState) -> ActuatorState:
    specs = state['spec_data']
    logs = []
    if specs.get('rated_torque_nm', 0) <= 0:
        logs.append('Invalid torque value')
    return {'validation_log': logs, 'is_compliant': len(logs) == 0}

def route_by_compliance(state: ActuatorState) -> str:
    return 'valid' if state['is_compliant'] else 'reject'

graph = StateGraph(ActuatorState)
graph.add_node('validate', validate_specs)
graph.add_edge('validate', END)
graph.set_entry_point('validate')
