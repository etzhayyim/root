from langgraph.graph import StateGraph, END
from typing import TypedDict, List

class DentalSupplyState(TypedDict):
    kit_id: str
    compliance_docs: List[str]
    is_validated: bool

def validate_certification(state: DentalSupplyState):
    state['is_validated'] = 'ISO13485' in state['compliance_docs']
    return state

def check_hygiene_standards(state: DentalSupplyState):
    return 'hygiene_passed' if state['is_validated'] else 'hygiene_failed'

graph = StateGraph(DentalSupplyState)
graph.add_node('validate', validate_certification)
graph.set_entry_point('validate')
graph.add_edge('validate', END)
