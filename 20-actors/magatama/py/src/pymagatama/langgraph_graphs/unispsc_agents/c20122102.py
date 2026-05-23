from typing import TypedDict, Annotated, Sequence
import operator
from langgraph.graph import StateGraph, END

class MotorProcurementState(TypedDict):
    spec_requirements: dict
    validation_logs: Annotated[list[str], operator.add]
    is_compliant: bool

def validate_specs(state: MotorProcurementState):
    specs = state['spec_requirements']
    logs = []
    compliant = True
    if specs.get('torque_rating_nm', 0) < 0.1:
        logs.append('Torque insufficient for heavy industrial application.')
        compliant = False
    return {'validation_logs': logs, 'is_compliant': compliant}

def check_dual_use(state: MotorProcurementState):
    logs = ['Checking dual-use export compliance.']
    return {'validation_logs': logs}

workflow = StateGraph(MotorProcurementState)
workflow.add_node('validate', validate_specs)
workflow.add_node('export_check', check_dual_use)
workflow.set_entry_point('validate')
workflow.add_edge('validate', 'export_check')
workflow.add_edge('export_check', END)
graph = workflow.compile()
