from typing import TypedDict, Annotated, Sequence
import operator
from langgraph.graph import StateGraph, END

class MetalPowderState(TypedDict):
    material_code: str
    purity_level: float
    particle_size: float
    is_validated: bool
    history: Annotated[Sequence[str], operator.add]

def validate_spec(state: MetalPowderState) -> MetalPowderState:
    # Specialized validation logic for high-purity metal powders
    state['is_validated'] = state['purity_level'] >= 99.9
    state['history'] = ['validation_completed']
    return state

def route_by_risk(state: MetalPowderState) -> str:
    return 'process_secure' if state['is_validated'] else 'reject_procurement'

workflow = StateGraph(MetalPowderState)
workflow.add_node('validate', validate_spec)
workflow.set_entry_point('validate')
workflow.add_conditional_edges('validate', route_by_risk)
workflow.add_edge('process_secure', END)
workflow.add_edge('reject_procurement', END)
graph = workflow.compile()