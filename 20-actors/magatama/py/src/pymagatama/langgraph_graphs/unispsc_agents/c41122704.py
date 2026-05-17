from typing import TypedDict, Annotated
from langgraph.graph import StateGraph, END

class TapeSupplyState(TypedDict):
    tape_spec: dict
    validation_result: bool
    compliance_check: str

def validate_tape_specs(state: TapeSupplyState):
    spec = state['tape_spec']
    is_valid = spec.get('adhesion_level') == 'high' and 'pattern' in spec
    return {'validation_result': is_valid}

def check_compliance(state: TapeSupplyState):
    return {'compliance_check': 'Certified for ISO 17712' if state['validation_result'] else 'Non-compliant'}

graph = StateGraph(TapeSupplyState)
graph.add_node('validate', validate_tape_specs)
graph.add_node('compliance', check_compliance)
graph.add_edge('validate', 'compliance')
graph.add_edge('compliance', END)
graph.set_entry_point('validate')
graph = graph.compile()