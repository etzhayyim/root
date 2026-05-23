from typing import TypedDict
from langgraph.graph import StateGraph, END

class VacuumCupState(TypedDict):
    material: str
    max_load: float
    validated: bool

def validate_material(state: VacuumCupState):
    allowed = ['NBR', 'Silicone', 'PU']
    return {'validated': state['material'] in allowed}

graph = StateGraph(VacuumCupState)
graph.add_node('validate', validate_material)
graph.set_entry_point('validate')
graph.add_edge('validate', END)
graph = graph.compile()
