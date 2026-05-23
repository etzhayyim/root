from langgraph.graph import StateGraph, END
from typing import TypedDict
class SpecState(TypedDict):
    spec_data: dict
    is_compliant: bool
def validate_sterile_spec(state: SpecState):
    spec = state['spec_data']
    is_compliant = spec.get('sterilization_method') in ['EO', 'Gamma'] and spec.get('material_composition') is not None
    return {'is_compliant': is_compliant}
workflow = StateGraph(SpecState)
workflow.add_node('validate', validate_sterile_spec)
workflow.set_entry_point('validate')
workflow.add_edge('validate', END)
graph = workflow.compile()
