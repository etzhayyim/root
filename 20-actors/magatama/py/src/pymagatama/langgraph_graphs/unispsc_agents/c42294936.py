from langgraph.graph import StateGraph, END
from typing import TypedDict

class EndoscopicState(TypedDict):
    spec_data: dict
    validation_flags: list

def validate_biocompatibility(state: EndoscopicState):
    state['validation_flags'].append('ISO_10993_Checked')
    return state

def inspect_channel_integrity(state: EndoscopicState):
    state['validation_flags'].append('Integrity_Verified')
    return state

graph = StateGraph(EndoscopicState)
graph.add_node('validate', validate_biocompatibility)
graph.add_node('integrity_check', inspect_channel_integrity)
graph.set_entry_point('validate')
graph.add_edge('validate', 'integrity_check')
graph.add_edge('integrity_check', END)
app = graph.compile()