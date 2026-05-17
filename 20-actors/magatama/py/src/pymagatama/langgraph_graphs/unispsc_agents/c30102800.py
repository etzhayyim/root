from typing import TypedDict
from langgraph.graph import StateGraph, END

class PilingState(TypedDict):
    order_specs: dict
    validation_result: bool
    approved: bool

def validate_structural_specs(state: PilingState):
    specs = state['order_specs']
    is_valid = 'material_grade' in specs and 'length_tolerance' in specs
    return {'validation_result': is_valid}

def check_compliance(state: PilingState):
    return {'approved': state['validation_result']}

graph = StateGraph(PilingState)
graph.add_node('validate', validate_structural_specs)
graph.add_node('compliance', check_compliance)
graph.set_entry_point('validate')
graph.add_edge('validate', 'compliance')
graph.add_edge('compliance', END)
graph = graph.compile()