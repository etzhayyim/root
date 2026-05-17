from typing import TypedDict
from langgraph.graph import StateGraph, END
class OzoneFilterState(TypedDict):
    spec_data: dict
    validation_passed: bool
def validate_tech_specs(state: OzoneFilterState):
    efficiency = state['spec_data'].get('eff', 0)
    return {'validation_passed': efficiency > 95.0}
def check_compliance(state: OzoneFilterState):
    return {'validation_passed': state['validation_passed'] and 'ISO' in state['spec_data'].get('certs', '')}
graph = StateGraph(OzoneFilterState)
graph.add_node('validate', validate_tech_specs)
graph.add_node('compliance', check_compliance)
graph.add_edge('validate', 'compliance')
graph.add_edge('compliance', END)
graph.set_entry_point('validate')
graph = graph.compile()