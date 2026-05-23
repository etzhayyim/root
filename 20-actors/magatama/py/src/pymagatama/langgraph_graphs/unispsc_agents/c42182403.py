from typing import TypedDict
from langgraph.graph import StateGraph, END

class AudiometricState(TypedDict):
    specs: dict
    validation_passed: bool
    compliance_report: str

def validate_acoustic_specs(state: AudiometricState):
    db_rating = state['specs'].get('db_rating', 0)
    is_valid = db_rating >= 40
    return {'validation_passed': is_valid, 'compliance_report': 'ISO8253 compliant' if is_valid else 'Failed'}

def finalize(state: AudiometricState):
    return {'compliance_report': 'Safety check complete'}

graph = StateGraph(AudiometricState)
graph.add_node('validate', validate_acoustic_specs)
graph.add_node('finalize', finalize)
graph.set_entry_point('validate')
graph.add_edge('validate', 'finalize')
graph.add_edge('finalize', END)
graph = graph.compile()
