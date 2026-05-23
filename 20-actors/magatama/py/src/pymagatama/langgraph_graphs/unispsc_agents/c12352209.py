from typing import TypedDict, Annotated, Sequence
import operator
from langgraph.graph import StateGraph, END

class CatalystState(TypedDict):
    batch_id: str
    purity_level: float
    validation_checks: Annotated[Sequence[str], operator.add]
    status: str

def validate_catalyst(state: CatalystState) -> CatalystState:
    checks = []
    if state['purity_level'] < 0.99:
        checks.append('FAILED_PURITY')
        status = 'REJECTED'
    else:
        checks.append('PASSED_QC')
        status = 'READY'
    return {'validation_checks': checks, 'status': status}

def prepare_logistics(state: CatalystState) -> CatalystState:
    if state['status'] == 'READY':
        return {'status': 'READY_FOR_SHIPMENT'}
    return {'status': 'LOGISTICS_PENDING'}

graph = StateGraph(CatalystState)
graph.add_node('qc', validate_catalyst)
graph.add_node('logistics', prepare_logistics)
graph.add_edge('qc', 'logistics')
graph.set_entry_point('qc')
graph.add_edge('logistics', END)
graph = graph.compile()
