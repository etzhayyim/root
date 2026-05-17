from typing import TypedDict, Annotated, Sequence
import operator
from langgraph.graph import StateGraph, END

class AdhesiveState(TypedDict):
    material_id: str
    batch_id: str
    viscosity: float
    curing_required: bool
    validation_logs: Annotated[Sequence[str], operator.add]

def validate_viscosity(state: AdhesiveState) -> AdhesiveState:
    if state['viscosity'] < 500 or state['viscosity'] > 5000:
        return {'validation_logs': ['Viscosity out of tolerance']}
    return {'validation_logs': ['Viscosity validated']}

def check_batch_compliance(state: AdhesiveState) -> AdhesiveState:
    return {'validation_logs': [f'Compliance check for batch {state["batch_id"]} passed']}

workflow = StateGraph(AdhesiveState)
workflow.add_node('viscosity_check', validate_viscosity)
workflow.add_node('compliance_check', check_batch_compliance)
workflow.set_entry_point('viscosity_check')
workflow.add_edge('viscosity_check', 'compliance_check')
workflow.add_edge('compliance_check', END)

graph = workflow.compile()