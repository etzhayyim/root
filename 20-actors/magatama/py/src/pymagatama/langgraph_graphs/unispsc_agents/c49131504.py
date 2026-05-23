from typing import TypedDict, List
from langgraph.graph import StateGraph, END

class FishingLureState(TypedDict):
    lure_id: str
    specifications: dict
    approved: bool

def validate_material(state: FishingLureState):
    # Business logic for material sustainability check
    return {'approved': 'non-toxic' in str(state['specifications'].get('material', ''))}

def finalize_lure_entry(state: FishingLureState):
    return {'approved': True}

graph = StateGraph(FishingLureState)
graph.add_node('validate', validate_material)
graph.add_node('finalize', finalize_lure_entry)
graph.add_edge('validate', 'finalize')
graph.add_edge('finalize', END)
graph.set_entry_point('validate')
app = graph.compile()
