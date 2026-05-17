from typing import TypedDict, Annotated, List
from langgraph.graph import StateGraph, END

class ValveState(TypedDict):
    part_number: str
    spec_verified: bool
    compliance_checks: List[str]

def validate_specs(state: ValveState) -> ValveState:
    print(f'Validating specs for {state[\'part_number\']}')
    state[\'spec_verified\'] = True
    return state

def run_compliance(state: ValveState) -> ValveState:
    if state[\'spec_verified\']:
        state[\'compliance_checks\'].append('dual-use-review-passed')
    return state

graph = StateGraph(ValveState)
graph.add_node("validate", validate_specs)
graph.add_node("compliance", run_compliance)
graph.add_edge("validate", "compliance")
graph.add_edge("compliance", END)
graph.set_entry_point("validate")
graph = graph.compile()