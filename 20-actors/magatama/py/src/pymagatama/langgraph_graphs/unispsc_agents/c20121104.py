from typing import TypedDict, Annotated, List
from langgraph.graph import StateGraph, END
from langgraph.graph.message import add_messages

class ActuatorState(TypedDict):
    actuator_id: str
    torque_requirements: float
    validation_passed: bool
    logs: Annotated[List[str], add_messages]

def validate_specs(state: ActuatorState):
    # Simulate CAD/Engineering Spec Validation
    is_valid = state['torque_requirements'] > 0
    return {'validation_passed': is_valid, 'logs': ['Spec validation complete.']}

def hardware_check(state: ActuatorState):
    return {'logs': ['Hardware stress test simulation finished.']}

def deploy_actuator(state: ActuatorState):
    return {'logs': ['Actuator ready for integration.']}

builder = StateGraph(ActuatorState)
builder.add_node('validate', validate_specs)
builder.add_node('hw_check', hardware_check)
builder.add_node('deploy', deploy_actuator)

builder.set_entry_point('validate')
builder.add_edge('validate', 'hw_check')
builder.add_edge('hw_check', 'deploy')
builder.add_edge('deploy', END)

graph = builder.compile()
