from typing import TypedDict
from langgraph.graph import StateGraph, END

class IrrigationState(TypedDict):
    device_id: str
    compliance_docs: list
    is_approved: bool

def validate_compliance(state: IrrigationState):
    print(f'Verifying medical certification for {state['device_id']}')
    return {'is_approved': len(state['compliance_docs']) > 0}

def update_records(state: IrrigationState):
    print('Finalizing procurement record.')
    return {}

graph = StateGraph(IrrigationState)
graph.add_node('validate', validate_compliance)
graph.add_node('record', update_records)
graph.add_edge('validate', 'record')
graph.add_edge('record', END)
graph.set_entry_point('validate')
graph = graph.compile()