from typing import TypedDict, List
from langgraph.graph import StateGraph, END

class ChemicalState(TypedDict):
    material_name: str
    concentration: float
    safety_clearance: bool
    hazard_verified: bool

def validate_safety(state: ChemicalState):
    print(f'Checking safety standards for {state.material_name}...')
    return {'hazard_verified': state['concentration'] < 37.0}

def approve_procurement(state: ChemicalState):
    print('Verification complete. Proceeding to safe storage protocol.')
    return {'safety_clearance': True}

graph = StateGraph(ChemicalState)
graph.add_node('safety_check', validate_safety)
graph.add_node('approval', approve_procurement)
graph.set_entry_point('safety_check')
graph.add_edge('safety_check', 'approval')
graph.add_edge('approval', END)
graph = graph.compile()
