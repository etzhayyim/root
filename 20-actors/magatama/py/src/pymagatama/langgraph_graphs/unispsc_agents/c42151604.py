from typing import TypedDict, List
from langgraph.graph import StateGraph, END

class CompositeToolState(TypedDict):
    tool_id: str
    spec_requirements: List[str]
    validation_passed: bool

def validate_tool_specs(state: CompositeToolState):
    print('Validating composite placement tool specs...')
    state['validation_passed'] = all(req in state['spec_requirements'] for req in ['accuracy', 'material'])
    return state

def check_compliance(state: CompositeToolState):
    print('Checking export control/dual-use compliance...')
    return 'compliant' if state['validation_passed'] else 'non-compliant'

builder = StateGraph(CompositeToolState)
builder.add_node('validate', validate_tool_specs)
builder.add_node('compliance', check_compliance)
builder.set_entry_point('validate')
builder.add_edge('validate', 'compliance')
builder.add_edge('compliance', END)
graph = builder.compile()
