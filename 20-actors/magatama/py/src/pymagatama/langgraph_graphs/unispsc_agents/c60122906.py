from typing import TypedDict
from langgraph.graph import StateGraph, END

class GlassBeadState(TypedDict):
    batch_id: str
    specifications: dict
    validation_status: bool

def validate_beads(state: GlassBeadState):
    specs = state.get('specifications', {})
    is_valid = all(k in specs for k in ['diameter', 'material', 'refractive_index'])
    print(f'Validating batch {state["batch_id"]}: {is_valid}')
    return {'validation_status': is_valid}

def process_batch(state: GlassBeadState):
    if state['validation_status']:
        print('Batch moving to quality assurance inspection.')
    return {'validation_status': True}

graph = StateGraph(GlassBeadState)
graph.add_node('validate', validate_beads)
graph.add_node('process', process_batch)
graph.set_entry_point('validate')
graph.add_edge('validate', 'process')
graph.add_edge('process', END)
graph = graph.compile()
