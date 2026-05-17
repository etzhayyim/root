from typing import TypedDict, List
from langgraph.graph import StateGraph, END

class ChemicalState(TypedDict):
    cas_number: str
    purity: float
    safety_clearance: bool
    validation_log: List[str]

def validate_purity(state: ChemicalState):
    state['validation_log'].append(f'Checking purity: {state.get("purity", 0)}%')
    return {"safety_clearance": state.get("purity", 0) > 99.0}

def check_regulatory(state: ChemicalState):
    state['validation_log'].append(f'Verifying CAS: {state.get("cas_number")}')
    return {"safety_clearance": state['safety_clearance'] and True}

graph = StateGraph(ChemicalState)
graph.add_node("purity_check", validate_purity)
graph.add_node("reg_check", check_regulatory)
graph.set_entry_point("purity_check")
graph.add_edge("purity_check", "reg_check")
graph.add_edge("reg_check", END)
app = graph.compile()