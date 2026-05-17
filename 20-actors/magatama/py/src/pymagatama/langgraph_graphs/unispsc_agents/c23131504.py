from typing import TypedDict
from langgraph.graph import StateGraph, END

class ProcurementState(TypedDict):
    part_id: str
    specs: dict
    approved: bool

def validate_specs(state: ProcurementState):
    # Business logic for machine tool component validation
    state['approved'] = all(k in state['specs'] for k in ['precision', 'material'])
    print(f'Validating components for {state.get("part_id")}...')
    return 'end'

graph = StateGraph(ProcurementState)
graph.add_node('validate', validate_specs)
graph.set_entry_point('validate')
graph.add_edge('validate', END)
app = graph.compile()