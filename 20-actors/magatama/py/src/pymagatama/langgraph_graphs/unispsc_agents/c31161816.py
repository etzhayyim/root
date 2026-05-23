from typing import TypedDict, Annotated
from langgraph.graph import StateGraph, END
class SpacerState(TypedDict):
    specs: dict
    validation_result: bool
    compliant: bool
def validate_specs(state: SpacerState):
    required = ['material', 'thread', 'length']
    valid = all(k in state['specs'] for k in required)
    return {'validation_result': valid}
def check_compliance(state: SpacerState):
    rohs = state['specs'].get('RoHS', True)
    return {'compliant': rohs}
graph = StateGraph(SpacerState)
graph.add_node('validate', validate_specs)
graph.add_node('compliance', check_compliance)
graph.add_edge('validate', 'compliance')
graph.add_edge('compliance', END)
graph.set_entry_point('validate')
graph = graph.compile()
