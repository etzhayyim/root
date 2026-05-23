from typing import TypedDict, Annotated, List
from langgraph.graph import StateGraph, END

class ChemicalState(TypedDict):
    material_id: str
    purity_level: float
    hazard_checks: List[str]
    is_cleared: bool

def validate_safety_protocols(state: ChemicalState):
    checks = state.get('hazard_checks', [])
    is_safe = 'SDS_Verified' in checks and 'Storage_Verified' in checks
    return {'is_cleared': is_safe}

def process_chemical(state: ChemicalState):
    if state['purity_level'] < 0.99:
        return {'hazard_checks': ['Requires_Purification']}
    return {'hazard_checks': ['Passed_Purity_Check']}

builder = StateGraph(ChemicalState)
builder.add_node('safety', validate_safety_protocols)
builder.add_node('process', process_chemical)
builder.set_entry_point('process')
builder.add_edge('process', 'safety')
builder.add_edge('safety', END)
graph = builder.compile()
