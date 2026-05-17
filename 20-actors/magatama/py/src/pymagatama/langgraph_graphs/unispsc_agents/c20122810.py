from typing import TypedDict, Annotated, Sequence
import operator
from langgraph.graph import StateGraph, END

class ActuatorState(TypedDict):
    spec_data: dict
    validation_log: Annotated[Sequence[str], operator.add]
    is_approved: bool

def validate_specs(state: ActuatorState):
    spec = state['spec_data']
    logs = []
    if spec.get('torque_capacity_nm', 0) <= 0:
        logs.append('Invalid torque capacity')
    if spec.get('ip_protection_rating', 0) < 54:
        logs.append('Insufficient IP rating for industrial use')
    return {'validation_log': logs, 'is_approved': len(logs) == 0}

def finalize_order(state: ActuatorState):
    return {'validation_log': ['Order processed to fulfillment']}

graph = StateGraph(ActuatorState)
graph.add_node('validate', validate_specs)
graph.add_node('finalize', finalize_order)
graph.set_entry_point('validate')
graph.add_edge('validate', 'finalize')
graph.add_edge('finalize', END)
graph = graph.compile()