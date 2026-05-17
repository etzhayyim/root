from typing import TypedDict, Annotated, List
from langgraph.graph import StateGraph, END
import operator

class ActuatorState(TypedDict):
    spec_requirements: dict
    validation_logs: Annotated[List[str], operator.add]
    is_compliant: bool

def validate_actuator_specs(state: ActuatorState):
    logs = []
    compliant = True
    torque = state['spec_requirements'].get('torque_nm', 0)
    if torque < 50:
        logs.append('Insufficient torque for industrial standard')
        compliant = False
    return {'validation_logs': logs, 'is_compliant': compliant}

def finalize_order(state: ActuatorState):
    return {'validation_logs': ['Order prepared for procurement']}

workflow = StateGraph(ActuatorState)
workflow.add_node('validate', validate_actuator_specs)
workflow.add_node('finalize', finalize_order)
workflow.set_entry_point('validate')
workflow.add_edge('validate', 'finalize')
workflow.add_edge('finalize', END)
graph = workflow.compile()