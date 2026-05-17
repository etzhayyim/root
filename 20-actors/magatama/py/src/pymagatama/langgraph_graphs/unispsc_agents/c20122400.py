from typing import TypedDict, Annotated, List
from langgraph.graph import StateGraph, END

class ActuatorState(TypedDict):
    spec_id: str
    validation_checks: List[str]
    is_compliant: bool

def validate_specs(state: ActuatorState):
    checks = []
    if 'operating_voltage_range' in state: checks.append('VOLTAGE_CHECK')
    if 'torque_specification' in state: checks.append('TORQUE_CHECK')
    return {**state, 'validation_checks': checks, 'is_compliant': len(checks) == 2}

def process_actuator(state: ActuatorState):
    print(f'Processing precision actuator {state["spec_id"]}')
    return state

builder = StateGraph(ActuatorState)
builder.add_node('validate', validate_specs)
builder.add_node('process', process_actuator)
builder.add_edge('validate', 'process')
builder.add_edge('process', END)
builder.set_entry_point('validate')
graph = builder.compile()