from typing import TypedDict
from langgraph.graph import StateGraph, END

class IlluminatorState(TypedDict):
    luminance_measured: float
    passes_inspection: bool
    compliance_record: str

def validate_luminance(state: IlluminatorState):
    target = 3000
    state['passes_inspection'] = state['luminance_measured'] >= target
    state['compliance_record'] = 'Verified' if state['passes_inspection'] else 'Failed'
    return state

graph = StateGraph(IlluminatorState)
graph.add_node('validate', validate_luminance)
graph.set_entry_point('validate')
graph.add_edge('validate', END)
graph = graph.compile()