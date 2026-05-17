from typing import TypedDict, Annotated, List
from langgraph.graph import StateGraph, END

class StationeryState(TypedDict):
    item_code: str
    quantity: int
    is_compliant: bool
    inspection_report: List[str]

def validate_supply(state: StationeryState):
    report = []
    compliant = True
    if state['quantity'] <= 0:
        report.append('Invalid quantity')
        compliant = False
    return {'is_compliant': compliant, 'inspection_report': report}

def process_procurement(state: StationeryState):
    return {'inspection_report': state['inspection_report'] + ['Supply chain verified']}

graph = StateGraph(StationeryState)
graph.add_node('validate', validate_supply)
graph.add_node('procure', process_procurement)
graph.add_edge('validate', 'procure')
graph.add_edge('procure', END)
graph.set_entry_point('validate')
graph = graph.compile()