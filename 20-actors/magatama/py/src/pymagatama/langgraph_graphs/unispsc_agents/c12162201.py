from typing import TypedDict, Annotated, Sequence
from langgraph.graph import StateGraph, END
import operator

class SilaneState(TypedDict):
    purity: float
    moisture_ppm: float
    validation_logs: Annotated[Sequence[str], operator.add]
    status: str

def validate_silane_specs(state: SilaneState):
    logs = []
    if state['purity'] < 99.5:
        logs.append(f'Low purity: {state['purity']}')
    if state['moisture_ppm'] > 500:
        logs.append(f'High moisture: {state['moisture_ppm']}')
    return {'validation_logs': logs, 'status': 'VALIDATED' if not logs else 'FAILED'}

def route_by_status(state: SilaneState):
    return 'process_shipment' if state['status'] == 'VALIDATED' else END

def process_shipment(state: SilaneState):
    return {'validation_logs': ['Shipment processing initiated']}

graph = StateGraph(SilaneState)
graph.add_node('validate', validate_silane_specs)
graph.add_node('process_shipment', process_shipment)
graph.set_entry_point('validate')
graph.add_conditional_edges('validate', route_by_status, {'process_shipment': 'process_shipment', '__end__': END})
graph.add_edge('process_shipment', END)
app = graph.compile()