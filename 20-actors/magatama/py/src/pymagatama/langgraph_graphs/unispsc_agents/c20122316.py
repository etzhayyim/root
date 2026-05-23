from typing import TypedDict, Annotated, Sequence
import operator
from langgraph.graph import StateGraph, END

class ServoProcState(TypedDict):
    spec_data: dict
    validation_log: Annotated[Sequence[str], operator.add]
    is_compliant: bool

def validate_servo_specs(state: ServoProcState):
    log = []
    specs = state['spec_data']
    if specs.get('torque_rating_nm', 0) <= 0:
        log.append('Invalid torque rating')
    return {'validation_log': log}

def check_compliance(state: ServoProcState):
    return {'is_compliant': len(state['validation_log']) == 0}

workflow = StateGraph(ServoProcState)
workflow.add_node('validate', validate_servo_specs)
workflow.add_node('check', check_compliance)
workflow.set_entry_point('validate')
workflow.add_edge('validate', 'check')
workflow.add_edge('check', END)
graph = workflow.compile()
