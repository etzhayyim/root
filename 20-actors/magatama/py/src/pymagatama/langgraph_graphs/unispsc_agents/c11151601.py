from typing import TypedDict, Annotated
from langgraph.graph import StateGraph, END

class SilicaIngestState(TypedDict):
    batch_id: str
    purity_level: float
    moisture_content: float
    status: str

def validate_purity(state: SilicaIngestState) -> SilicaIngestState:
    if state['purity_level'] < 99.9:
        state['status'] = 'REJECTED_PURITY'
    else:
        state['status'] = 'VALIDATED'
    return state

def check_moisture(state: SilicaIngestState) -> SilicaIngestState:
    if state['moisture_content'] > 0.5:
        state['status'] = 'NEEDS_DRYING'
    return state

graph = StateGraph(SilicaIngestState)
graph.add_node('validate_purity', validate_purity)
graph.add_node('check_moisture', check_moisture)
graph.set_entry_point('validate_purity')
graph.add_edge('validate_purity', 'check_moisture')
graph.add_edge('check_moisture', END)

compiled_graph = graph.compile()
