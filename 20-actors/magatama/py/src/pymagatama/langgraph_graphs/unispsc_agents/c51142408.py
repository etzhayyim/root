from typing import TypedDict
from langgraph.graph import StateGraph, END

class PharmaState(TypedDict):
    batch_id: str
    compliance_status: bool
    temperature_check: bool

def validate_batch(state: PharmaState):
    print(f'Validating batch {state["batch_id"]} against pharmacopeia standards...')
    return {'compliance_status': True}

def verify_storage(state: PharmaState):
    print('Verifying cold chain logs for frovatriptan...')
    return {'temperature_check': True}

graph = StateGraph(PharmaState)
graph.add_node('validate', validate_batch)
graph.add_node('storage', verify_storage)
graph.set_entry_point('validate')
graph.add_edge('validate', 'storage')
graph.add_edge('storage', END)
compile = graph.compile()