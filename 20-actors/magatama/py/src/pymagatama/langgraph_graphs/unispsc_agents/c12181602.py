from typing import TypedDict, Annotated, List
from langgraph.graph import StateGraph, END

class ChemicalProcurementState(TypedDict):
    cas_number: str
    purity: float
    storage_temp: float
    is_approved: bool

def validate_purity(state: ChemicalProcurementState) -> dict:
    return {'is_approved': state['purity'] >= 99.9}

def check_hazmat(state: ChemicalProcurementState) -> dict:
    # Logic for specialized handling protocols
    return {'is_approved': state['is_approved'] and state['storage_temp'] <= -20.0}

graph = StateGraph(ChemicalProcurementState)
graph.add_node('validate_purity', validate_purity)
graph.add_node('check_hazmat', check_hazmat)
graph.add_edge('validate_purity', 'check_hazmat')
graph.add_edge('check_hazmat', END)
graph.set_entry_point('validate_purity')
app = graph.compile()
