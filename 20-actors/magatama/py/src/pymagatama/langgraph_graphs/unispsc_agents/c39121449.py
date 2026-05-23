from typing import TypedDict
from langgraph.graph import StateGraph, END

class ConnectorState(TypedDict):
    spec_data: dict
    validation_passed: bool

def validate_connector_specs(state: ConnectorState):
    required = ['gauge', 'voltage', 'material']
    valid = all(k in state['spec_data'] for k in required)
    return {'validation_passed': valid}

def compliance_check(state: ConnectorState):
    print('Checking regulatory compliance for connector...')
    return {'validation_passed': True}

graph = StateGraph(ConnectorState)
graph.add_node('validate', validate_connector_specs)
graph.add_node('compliance', compliance_check)
graph.set_entry_point('validate')
graph.add_edge('validate', 'compliance')
graph.add_edge('compliance', END)
graph = graph.compile()
