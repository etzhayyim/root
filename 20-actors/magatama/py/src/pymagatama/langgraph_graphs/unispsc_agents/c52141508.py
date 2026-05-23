from typing import TypedDict, List
from langgraph.graph import StateGraph, END

class FreezerState(TypedDict):
    model_number: str
    volume: float
    energy_rating: str
    is_compliant: bool

def validate_specs(state: FreezerState):
    state['is_compliant'] = state['volume'] > 0 and state['energy_rating'] in ['A', 'B', 'C']
    return state

workflow = StateGraph(FreezerState)
workflow.add_node('validate', validate_specs)
workflow.set_entry_point('validate')
workflow.add_edge('validate', END)
graph = workflow.compile()
