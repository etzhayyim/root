from typing import TypedDict, Annotated
from langgraph.graph import StateGraph, END

class PaperState(TypedDict):
    paper_id: str
    weight: int
    brightness: int
    is_verified: bool

def validate_paper_spec(state: PaperState) -> PaperState:
    # Logic to validate paper specifications against procurement requirements
    state['is_verified'] = (state['weight'] >= 70 and state['brightness'] >= 90)
    return state

def process_procurement(state: PaperState) -> PaperState:
    if state['is_verified']:
        print(f'Paper {state['paper_id']} approved for procurement.')
    else:
        print(f'Paper {state['paper_id']} rejected due to spec mismatch.')
    return state

graph = StateGraph(PaperState)
graph.add_node('validate', validate_paper_spec)
graph.add_node('process', process_procurement)
graph.add_edge('validate', 'process')
graph.add_edge('process', END)
graph.set_entry_point('validate')
graph = graph.compile()
