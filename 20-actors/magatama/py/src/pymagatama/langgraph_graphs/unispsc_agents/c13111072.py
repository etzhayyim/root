from typing import TypedDict, Annotated, Sequence
from langgraph.graph import StateGraph, END
import operator

class AbrasiveState(TypedDict):
    material_id: str
    purity_level: float
    processing_steps: Annotated[Sequence[str], operator.add]

def validate_material(state: AbrasiveState):
    if state['purity_level'] < 0.95:
        return {'processing_steps': ['REJECTED: Low purity']}
    return {'processing_steps': ['VALIDATED: Proceed to grinding']}

def perform_grinding(state: AbrasiveState):
    return {'processing_steps': ['COMPLETED: Precision grinding sequence']}

graph = StateGraph(AbrasiveState)
graph.add_node('validate', validate_material)
graph.add_node('grind', perform_grinding)
graph.add_edge('validate', 'grind')
graph.add_edge('grind', END)
graph.set_entry_point('validate')
graph = graph.compile()