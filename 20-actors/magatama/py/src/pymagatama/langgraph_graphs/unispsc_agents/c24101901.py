from typing import TypedDict
from langgraph.graph import StateGraph, END

class DrumOpenerState(TypedDict):
    spec_data: dict
    validation_passed: bool

def validate_specs(state: DrumOpenerState):
    # Validate material and explosion proof standards
    if 'material' in state['spec_data'] and 'explosion_proof' in state['spec_data']:
        return {'validation_passed': True}
    return {'validation_passed': False}

def finalize_procurement(state: DrumOpenerState):
    print('Procurement request processed for drum opener.')
    return {}

graph = StateGraph(DrumOpenerState)
graph.add_node('validate', validate_specs)
graph.add_node('finalize', finalize_procurement)
graph.set_entry_point('validate')
graph.add_edge('validate', 'finalize')
graph.add_edge('finalize', END)
graph = graph.compile()