from typing import TypedDict, Annotated, List
from langgraph.graph import StateGraph, END

class MetalPowderState(TypedDict):
    commodity_code: str
    purity: float
    particle_size: float
    status: str
    validation_log: List[str]

def validate_specs(state: MetalPowderState):
    log = []
    if state['purity'] < 99.9:
        log.append('Purity below threshold')
    return {'validation_log': log, 'status': 'validated' if not log else 'rejected'}

def packing_logic(state: MetalPowderState):
    return {'status': 'ready_for_dispatch' if state['status'] == 'validated' else 'hold'}

builder = StateGraph(MetalPowderState)
builder.add_node('validate', validate_specs)
builder.add_node('pack', packing_logic)
builder.add_edge('validate', 'pack')
builder.add_edge('pack', END)
builder.set_entry_point('validate')
graph = builder.compile()
