from typing import TypedDict
from langgraph.graph import StateGraph, END

class HearingControlState(TypedDict):
    spec_data: dict
    validated: bool

def validate_acoustic_specs(state: HearingControlState):
    nrr = state['spec_data'].get('NRR_rating_db', 0)
    state['validated'] = nrr >= 20
    return state

workflow = StateGraph(HearingControlState)
workflow.add_node('validate', validate_acoustic_specs)
workflow.set_entry_point('validate')
workflow.add_edge('validate', END)
graph = workflow.compile()