from typing import TypedDict
from langgraph.graph import StateGraph, END

class SurgicalCapState(TypedDict):
    spec_data: dict
    validation_passed: bool

def validate_biocompatibility(state: SurgicalCapState):
    bio_docs = state['spec_data'].get('biocompatibility_certificate')
    return {'validation_passed': bio_docs is not None}

def check_sterilization(state: SurgicalCapState):
    is_sterile = state['spec_data'].get('sterilization_compatibility', False)
    return {'validation_passed': state['validation_passed'] and is_sterile}

graph = StateGraph(SurgicalCapState)
graph.add_node('validate_bio', validate_biocompatibility)
graph.add_node('check_steril', check_sterilization)
graph.set_entry_point('validate_bio')
graph.add_edge('validate_bio', 'check_steril')
graph.add_edge('check_steril', END)
graph = graph.compile()
