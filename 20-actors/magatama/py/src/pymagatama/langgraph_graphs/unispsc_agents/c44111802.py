from typing import TypedDict
from langgraph.graph import StateGraph, END
class DraftingFilmState(TypedDict):
    spec_sheet: dict
    approved: bool
def validate_specs(state: DraftingFilmState):
    thickness = state['spec_sheet'].get('thickness', 0)
    state['approved'] = 50 <= thickness <= 200
    return state
graph = StateGraph(DraftingFilmState)
graph.add_node('validate', validate_specs)
graph.set_entry_point('validate')
graph.add_edge('validate', END)
app = graph.compile()