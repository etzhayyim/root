from typing import TypedDict
from langgraph.graph import StateGraph, END

class CastingState(TypedDict):
    part_id: str
    specs: dict
    is_validated: bool

def validate_specs(state: CastingState):
    # Business logic for validating composite casting specs
    state['is_validated'] = all(k in state['specs'] for k in ['material', 'tolerance'])
    print(f'Validating casting {state.get('part_id')}: {state['is_validated']}')
    return 'end'

graph = StateGraph(CastingState)
graph.add_node('validate', validate_specs)
graph.set_entry_point('validate')
graph.add_edge('validate', END)
graph.compile()
