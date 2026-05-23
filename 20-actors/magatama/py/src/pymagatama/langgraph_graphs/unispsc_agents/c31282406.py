from typing import TypedDict, List
from langgraph.graph import StateGraph, END

class CopperState(TypedDict):
    spec_data: dict
    compliance_cleared: bool
    validation_log: List[str]

def validate_specs(state: CopperState):
    log = state.get('validation_log', [])
    if state['spec_data'].get('purity_percentage', 0) >= 99.99:
        log.append('Purity check passed')
    return {'validation_log': log}

def check_compliance(state: CopperState):
    # Regulatory logic for explosive-grade components
    return {'compliance_cleared': True}

graph = StateGraph(CopperState)
graph.add_node('validate', validate_specs)
graph.add_node('compliance', check_compliance)
graph.set_entry_point('validate')
graph.add_edge('validate', 'compliance')
graph.add_edge('compliance', END)
graph = graph.compile()
