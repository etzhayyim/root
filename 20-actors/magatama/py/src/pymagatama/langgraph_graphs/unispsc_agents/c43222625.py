from typing import TypedDict
from langgraph.graph import StateGraph, END
class AccessServerState(TypedDict):
    spec_data: dict
    validation_passed: bool
def validate_specs(state: AccessServerState):
    has_ram = 'ram_capacity' in state['spec_data']
    has_encryption = state['spec_data'].get('encryption_protocol_support')
    return {'validation_passed': bool(has_ram and has_encryption)}
def security_compliance(state: AccessServerState):
    print('Checking dual-use export and encryption compliance...')
    return {'validation_passed': state['validation_passed']}
graph = StateGraph(AccessServerState)
graph.add_node('validate', validate_specs)
graph.add_node('compliance', security_compliance)
graph.set_entry_point('validate')
graph.add_edge('validate', 'compliance')
graph.add_edge('compliance', END)
app = graph.compile()
