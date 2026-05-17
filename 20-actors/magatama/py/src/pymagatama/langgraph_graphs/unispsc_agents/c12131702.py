from typing import TypedDict, Annotated, Sequence
from langgraph.graph import StateGraph, END
import operator

class ReagentState(TypedDict):
    reagent_id: str
    purity_check: bool
    safety_clearance: bool
    final_approval: bool

def validate_purity(state: ReagentState):
    # Simulated complex analytical validation logic
    print(f'Validating purity for {state['reagent_id']}')
    return {'purity_check': True}

def perform_safety_audit(state: ReagentState):
    print(f'Running dual-use export control audit for {state['reagent_id']}')
    return {'safety_clearance': True}

def finalize_procurement(state: ReagentState):
    approved = state['purity_check'] and state['safety_clearance']
    return {'final_approval': approved}

graph = StateGraph(ReagentState)
graph.add_node('validate_purity', validate_purity)
graph.add_node('safety_audit', perform_safety_audit)
graph.add_node('finalize', finalize_procurement)

graph.set_entry_point('validate_purity')
graph.add_edge('validate_purity', 'safety_audit')
graph.add_edge('safety_audit', 'finalize')
graph.add_edge('finalize', END)

compiled_graph = graph.compile()