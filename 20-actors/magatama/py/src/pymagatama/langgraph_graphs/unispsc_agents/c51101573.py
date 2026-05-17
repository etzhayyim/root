from typing import TypedDict, Annotated, Sequence
import operator
from langgraph.graph import StateGraph, END

class PreservationState(TypedDict):
    vial_id: str
    cryogenic_temp: float
    qc_passed: bool
    log_history: Annotated[Sequence[str], operator.add]

def validate_vial(state: PreservationState) -> PreservationState:
    # Simplified validation logic for cryogenic vials
    is_valid = state.get('cryogenic_temp', 0) <= -150.0
    return {**state, 'qc_passed': is_valid, 'log_history': [f'Vial {state["vial_id"]} QC: {is_valid}']}

def storage_step(state: PreservationState) -> PreservationState:
    return {**state, 'log_history': ['Allocated to cryogenic storage vault']}

graph = StateGraph(PreservationState)
graph.add_node('validate', validate_vial)
graph.add_node('storage', storage_step)
graph.add_edge('validate', 'storage')
graph.add_edge('storage', END)
graph.set_entry_point('validate')
graph = graph.compile()