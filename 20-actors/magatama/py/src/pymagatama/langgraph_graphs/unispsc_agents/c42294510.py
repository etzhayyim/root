from typing import TypedDict
from langgraph.graph import StateGraph, END

class OphthalmicSpongeState(TypedDict):
    spec_data: dict
    validation_passed: bool
    is_sterile: bool

def validate_sponge_spec(state: OphthalmicSpongeState):
    spec = state['spec_data']
    state['validation_passed'] = (spec.get('sterilization_method') == 'gamma') and (spec.get('abs_rate_ml') > 5.0)
    return state

def check_compliance(state: OphthalmicSpongeState):
    state['is_sterile'] = state['spec_data'].get('iso_13485_certified', False)
    return state

graph = StateGraph(OphthalmicSpongeState)
graph.add_node('validate', validate_sponge_spec)
graph.add_node('compliance', check_compliance)
graph.set_entry_point('validate')
graph.add_edge('validate', 'compliance')
graph.add_edge('compliance', END)
app = graph.compile()
