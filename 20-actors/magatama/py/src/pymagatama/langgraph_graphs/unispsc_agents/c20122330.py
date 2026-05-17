from typing import TypedDict, Annotated, Sequence
import operator
from langgraph.graph import StateGraph, END

class ActuatorState(TypedDict):
    spec_data: dict
    validation_logs: Annotated[Sequence[str], operator.add]
    is_compliant: bool

def validate_specs(state: ActuatorState):
    specs = state['spec_data']
    logs = []
    if specs.get('torque', 0) < 0:
        logs.append('Invalid torque rating.')
    return {'validation_logs': logs}

def integration_check(state: ActuatorState):
    logs = ['Protocol verified.' if 'bus' in state['spec_data'] else 'Missing protocol.']
    return {'validation_logs': logs, 'is_compliant': True}

graph = StateGraph(ActuatorState)
graph.add_node('validate', validate_specs)
graph.add_node('integration', integration_check)
graph.set_entry_point('validate')
graph.add_edge('validate', 'integration')
graph.add_edge('integration', END)
graph = graph.compile()