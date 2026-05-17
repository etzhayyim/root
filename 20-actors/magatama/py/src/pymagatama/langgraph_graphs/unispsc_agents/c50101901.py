from typing import TypedDict, List
from langgraph.graph import StateGraph, END

class SupplyState(TypedDict):
    commodity: str
    quality_passed: bool
    temp_log: List[float]
    status: str

def validate_freshness(state: SupplyState):
    avg_temp = sum(state['temp_log']) / len(state['temp_log']) if state['temp_log'] else 10.0
    return {'quality_passed': avg_temp < 4.0, 'status': 'VALIDATED' if avg_temp < 4.0 else 'REJECTED'}

def process_shipment(state: SupplyState):
    return {'status': 'READY_FOR_DISTRIBUTION' if state['quality_passed'] else 'DISCARD'}

graph = StateGraph(SupplyState)
graph.add_node('validate', validate_freshness)
graph.add_node('process', process_shipment)
graph.add_edge('validate', 'process')
graph.add_edge('process', END)
graph.set_entry_point('validate')
graph = graph.compile()