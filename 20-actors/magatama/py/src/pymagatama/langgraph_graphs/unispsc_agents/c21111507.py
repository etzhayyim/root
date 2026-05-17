from typing import TypedDict
from langgraph.graph import StateGraph, END

class TractorState(TypedDict):
    specs: dict
    validation_status: str

def validate_specs(state: TractorState):
    hp = state['specs'].get('hp', 0)
    if hp < 20: return {'validation_status': 'REJECTED:Insufficient Power'}
    return {'validation_status': 'APPROVED'}

graph = StateGraph(TractorState)
graph.add_node('validate', validate_specs)
graph.set_entry_point('validate')
graph.add_edge('validate', END)
graph = graph.compile()