from typing import TypedDict, List
from langgraph.graph import StateGraph, END

class CleaningDeviceState(TypedDict):
    device_id: str
    compliance_docs: List[str]
    validation_status: bool

def validate_specs(state: CleaningDeviceState):
    print(f'Validating specs for {state['device_id']}')
    return {'validation_status': True}

def check_compliance(state: CleaningDeviceState):
    print('Checking ISO compliance certificate')
    return {'compliance_docs': ['ISO-15883']}

graph = StateGraph(CleaningDeviceState)
graph.add_node('validate', validate_specs)
graph.add_node('compliance', check_compliance)
graph.set_entry_point('compliance')
graph.add_edge('compliance', 'validate')
graph.add_edge('validate', END)
graph = graph.compile()