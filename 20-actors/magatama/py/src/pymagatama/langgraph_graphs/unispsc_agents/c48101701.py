from typing import TypedDict
from langgraph.graph import StateGraph, END

class DispenserState(TypedDict):
    model_number: str
    sanitation_certified: bool
    pressure_tested: bool

def validate_specs(state: DispenserState):
    if state.get('sanitation_certified') and state.get('pressure_tested'):
        return 'approved'
    return 'rejected'

workflow = StateGraph(DispenserState)
workflow.add_node('validation', validate_specs)
workflow.set_entry_point('validation')
workflow.add_edge('validation', END)
graph = workflow.compile()