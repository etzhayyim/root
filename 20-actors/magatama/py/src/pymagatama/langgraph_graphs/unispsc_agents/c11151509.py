from typing import TypedDict, Annotated
from langgraph.graph import StateGraph, END
from langgraph.graph.message import add_messages

class GasSupplyState(TypedDict):
    gas_spec: dict
    safety_check: bool
    logistics_status: str

def validate_safety_compliance(state: GasSupplyState) -> GasSupplyState:
    # Logic to verify container pressure and safety certification
    state['safety_check'] = state['gas_spec'].get('pressure', 0) < 300
    return state

def process_delivery(state: GasSupplyState) -> GasSupplyState:
    # Logic for specialized hazardous material logistics
    state['logistics_status'] = 'COMPLIANT_LOGISTICS_READY' if state['safety_check'] else 'REJECTED_SAFETY_VIOLATION'
    return state

graph = StateGraph(GasSupplyState)
graph.add_node('safety_check', validate_safety_compliance)
graph.add_node('logistics', process_delivery)
graph.add_edge('safety_check', 'logistics')
graph.add_edge('logistics', END)
graph.set_entry_point('safety_check')
graph = graph.compile()