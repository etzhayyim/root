from langgraph.graph import StateGraph, END
from typing import TypedDict, List

class SteelShotState(TypedDict):
    hardness: float
    size_range: str
    compliance_report: str
    approved: bool

def validate_specs(state: SteelShotState):
    # Business logic for ISO 11124-3 validation
    if 40 <= state['hardness'] <= 65:
        return {'approved': True}
    return {'approved': False}

def process_procurement(state: SteelShotState):
    print(f'Processing steel shot purchase for batch: {state}')
    return state

graph = StateGraph(SteelShotState)
graph.add_node('validate', validate_specs)
graph.add_node('process', process_procurement)
graph.set_entry_point('validate')
graph.add_edge('validate', 'process')
graph.add_edge('process', END)
graph = graph.compile()