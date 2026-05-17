from typing import TypedDict, Annotated, List
from langgraph.graph import StateGraph, END

class MineralProcState(TypedDict):
    commodity_id: str
    batch_id: str
    purity_validated: bool
    compliance_cleared: bool

def validate_purity(state: MineralProcState) -> MineralProcState:
    print(f'Validating purity for {state[\'batch_id\']}')
    state[\'purity_validated\'] = True
    return state

def check_compliance(state: MineralProcState) -> MineralProcState:
    print(f'Checking chemical compliance for {state[\'batch_id\']}')
    state[\'compliance_cleared\'] = True
    return state

graph = StateGraph(MineralProcState)
graph.add_node("validate", validate_purity)
graph.add_node("compliance", check_compliance)
graph.set_entry_point("validate")
graph.add_edge("validate", "compliance")
graph.add_edge("compliance", END)
graph = graph.compile()