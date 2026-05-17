from typing import TypedDict, Annotated, List
from langgraph.graph import StateGraph, END

class CrudeOilState(TypedDict):
    commodity_code: str
    batch_id: str
    purity_level: float
    safety_clearance: bool
    validation_logs: List[str]

def validate_cargo_safety(state: CrudeOilState) -> CrudeOilState:
    if state['purity_level'] < 0.95:
        state['validation_logs'].append('Purity check failed: Below industrial grade.')
        state['safety_clearance'] = False
    else:
        state['validation_logs'].append('Purity validated.')
    return state

def route_processing(state: CrudeOilState):
    return 'process' if state['safety_clearance'] else END

def process_crude_refinement(state: CrudeOilState) -> CrudeOilState:
    state['validation_logs'].append('Refinement parameters optimized for crude grade.')
    return state

builder = StateGraph(CrudeOilState)
builder.add_node('validate', validate_cargo_safety)
builder.add_node('process', process_crude_refinement)
builder.set_entry_point('validate')
builder.add_conditional_edges('validate', route_processing)
builder.add_edge('process', END)
graph = builder.compile()