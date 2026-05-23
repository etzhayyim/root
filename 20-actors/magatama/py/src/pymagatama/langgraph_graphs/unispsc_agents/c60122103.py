from langgraph.graph import StateGraph, END
from typing import TypedDict, List

class CandleState(TypedDict):
    material_type: str
    flash_point: float
    compliant: bool

def validate_materials(state: CandleState):
    if state['flash_point'] < 60:
        return {'compliant': False}
    return {'compliant': True}

graph = StateGraph(CandleState)
graph.add_node('validate', validate_materials)
graph.set_entry_point('validate')
graph.add_edge('validate', END)
graph = graph.compile()
