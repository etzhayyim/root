from typing import TypedDict, Annotated, Sequence, List
from langgraph.graph import StateGraph, END
from langgraph.graph.message import add_messages

class NitrogenProcurementState(TypedDict):
    purity: float
    volume: float
    is_liquid: bool
    validation_logs: List[str]
    approved: bool

def validate_purity(state: NitrogenProcurementState) -> NitrogenProcurementState:
    if state['purity'] < 99.9:
        state['validation_logs'].append('Low purity: requires additional purification steps.')
    else:
        state['validation_logs'].append('Purity check passed.')
    return state

def safety_protocol_check(state: NitrogenProcurementState) -> NitrogenProcurementState:
    if state['is_liquid']:
        state['validation_logs'].append('Handling as cryogenic dangerous good.')
    else:
        state['validation_logs'].append('Standard gas pressure check.')
    state['approved'] = True
    return state

builder = StateGraph(NitrogenProcurementState)
builder.add_node('validate_purity', validate_purity)
builder.add_node('safety_check', safety_protocol_check)
builder.add_edge('validate_purity', 'safety_check')
builder.add_edge('safety_check', END)
builder.set_entry_point('validate_purity')
graph = builder.compile()
