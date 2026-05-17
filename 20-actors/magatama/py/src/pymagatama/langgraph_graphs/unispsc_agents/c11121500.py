from typing import TypedDict, Annotated, Sequence
from langgraph.graph import StateGraph, END
from langgraph.graph.message import add_messages

class MineralProcessState(TypedDict):
    mineral_type: str
    quality_data: dict
    validation_passed: bool
    messages: Annotated[Sequence[str], add_messages]

def validate_purity(state: MineralProcessState) -> MineralProcessState:
    purity = state['quality_data'].get('purity', 0)
    state['validation_passed'] = purity >= 98.0
    state['messages'].append(f'Purity check result: {state['validation_passed']}')
    return state

def logistics_planning(state: MineralProcessState) -> MineralProcessState:
    if state['validation_passed']:
        state['messages'].append('Logistics routing initialized.')
    else:
        state['messages'].append('Logistics hold: quality failure.')
    return state

builder = StateGraph(MineralProcessState)
builder.add_node('validate', validate_purity)
builder.add_node('logistics', logistics_planning)
builder.set_entry_point('validate')
builder.add_edge('validate', 'logistics')
builder.add_edge('logistics', END)
graph = builder.compile()