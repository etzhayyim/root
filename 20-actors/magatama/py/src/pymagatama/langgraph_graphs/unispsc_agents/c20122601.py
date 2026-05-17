from typing import TypedDict, Annotated, List
from langgraph.graph import StateGraph, END

class ReducerState(TypedDict):
    part_number: str
    torque_requirements: float
    validation_checks: List[str]
    is_approved: bool

def validate_specs(state: ReducerState):
    checks = []
    if state['torque_requirements'] > 0:
        checks.append('TORQUE_PASSED')
    return {'validation_checks': checks}

def approve_procurement(state: ReducerState):
    return {'is_approved': len(state['validation_checks']) > 0}

workflow = StateGraph(ReducerState)
workflow.add_node('validate', validate_specs)
workflow.add_node('approve', approve_procurement)
workflow.add_edge('validate', 'approve')
workflow.add_edge('approve', END)
workflow.set_entry_point('validate')
graph = workflow.compile()