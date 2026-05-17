from typing import TypedDict
from langgraph.graph import StateGraph, END

class ServoState(TypedDict):
    specs: dict
    validation_result: bool
    compliance_report: str

def validate_specs(state: ServoState):
    required = ['InputVoltageRange', 'CommunicationProtocol']
    valid = all(key in state['specs'] for key in required)
    return {'validation_result': valid, 'compliance_report': 'Validated' if valid else 'Missing specs'}

def route_by_compliance(state: ServoState):
    return 'process' if state['validation_result'] else END

graph = StateGraph(ServoState)
graph.add_node('validate', validate_specs)
graph.add_node('process', lambda s: {'compliance_report': 'Processing servo firmware compilation'})
graph.add_edge('validate', 'process')
graph.add_edge('process', END)
graph.set_entry_point('validate')
app = graph.compile()