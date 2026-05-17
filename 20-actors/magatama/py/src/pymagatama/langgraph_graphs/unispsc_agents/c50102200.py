from typing import TypedDict, List
from langgraph.graph import StateGraph, END

class FruitProcurementState(TypedDict):
    origin: str
    brix_level: float
    temp_records: List[float]
    is_compliant: bool

def validate_quality(state: FruitProcurementState):
    if state['brix_level'] >= 12.0 and all(t <= 10.0 for t in state['temp_records']):
        return {'is_compliant': True}
    return {'is_compliant': False}

graph = StateGraph(FruitProcurementState)
graph.add_node('qc_check', validate_quality)
graph.set_entry_point('qc_check')
graph.add_edge('qc_check', END)
graph = graph.compile()