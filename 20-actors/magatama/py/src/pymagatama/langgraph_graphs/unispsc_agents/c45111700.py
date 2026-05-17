from typing import TypedDict
from langgraph.graph import StateGraph, END
class AudioGearState(TypedDict):
    equipment_id: str
    specs: dict
    validation_passed: bool
def validate_specs(state: AudioGearState):
    state['validation_passed'] = 'latency_specs' in state['specs']
    return state
def check_compliance(state: AudioGearState):
    return 'compliant' if state['validation_passed'] else 'needs_review'
graph = StateGraph(AudioGearState)
graph.add_node('validate', validate_specs)
graph.add_node('compliance', check_compliance)
graph.set_entry_point('validate')
graph.add_edge('validate', 'compliance')
graph.add_edge('compliance', END)
graph = graph.compile()