from typing import TypedDict, Annotated, List
from langgraph.graph import StateGraph, END

class FiberState(TypedDict):
    batch_id: str
    specifications: dict
    validation_passed: bool
    log: List[str]

def validate_fiber_specs(state: FiberState) -> FiberState:
    specs = state.get('specifications', {})
    # Logic: Validate structural integrity requirements
    if specs.get('tensile_strength', 0) > 3000:
        state['validation_passed'] = True
        state['log'].append('Quality check passed.')
    else:
        state['validation_passed'] = False
        state['log'].append('Quality check failed: insufficient tensile strength.')
    return state

def route_procurement(state: FiberState) -> str:
    return 'VALIDATE' if state['validation_passed'] else 'REJECT'

def finalize_order(state: FiberState) -> FiberState:
    state['log'].append('Procurement order finalized.')
    return state

graph = StateGraph(FiberState)
graph.add_node('VALIDATE', validate_fiber_specs)
graph.add_node('FINALIZE', finalize_order)
graph.set_entry_point('VALIDATE')
graph.add_conditional_edges('VALIDATE', route_procurement, {'VALIDATE': 'FINALIZE', 'REJECT': END})
graph.add_edge('FINALIZE', END)
compiled_graph = graph.compile()
