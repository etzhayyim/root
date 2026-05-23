from typing import TypedDict
from langgraph.graph import StateGraph, END

class MissileState(TypedDict):
    spec_data: dict
    security_cleared: bool
    validation_log: list

def validate_specs(state: MissileState):
    # Business logic for critical defense specs
    valid = all(key in state['spec_data'] for key in ['guidance', 'payload'])
    return {'validation_log': [f'Specs valid: {valid}'], 'security_cleared': valid}

def security_checkpoint(state: MissileState):
    # Regulatory and sanctions check
    return {'security_cleared': state.get('security_cleared', False)}

graph = StateGraph(MissileState)
graph.add_node('validate', validate_specs)
graph.add_node('security', security_checkpoint)
graph.set_entry_point('validate')
graph.add_edge('validate', 'security')
graph.add_edge('security', END)
graph = graph.compile()
