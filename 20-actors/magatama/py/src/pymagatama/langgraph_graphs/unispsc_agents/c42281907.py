from typing import TypedDict
from langgraph.graph import StateGraph, END
class InstrumentState(TypedDict):
    part_number: str
    material: str
    is_validated: bool
def validate_materials(state: InstrumentState):
    allowed = ['silicone', 'polypropylene']
    state['is_validated'] = state['material'].lower() in allowed
    return state
graph = StateGraph(InstrumentState)
graph.add_node('validate', validate_materials)
graph.set_entry_point('validate')
graph.add_edge('validate', END)
graph = graph.compile()