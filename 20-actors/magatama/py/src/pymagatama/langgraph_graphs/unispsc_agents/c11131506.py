from typing import TypedDict, Annotated, List
from langgraph.graph import StateGraph, END

class MineralProcessState(TypedDict):
    material_id: str
    purity: float
    process_steps: List[str]
    is_approved: bool

def validate_purity(state: MineralProcessState):
    state['is_approved'] = state['purity'] >= 99.5
    return state

def define_process(state: MineralProcessState):
    state['process_steps'] = ['cleaning', 'grinding', 'surface_inspection']
    return state

graph = StateGraph(MineralProcessState)
graph.add_node('validate', validate_purity)
graph.add_node('define', define_process)
graph.set_entry_point('validate')
graph.add_edge('validate', 'define')
graph.add_edge('define', END)
graph = graph.compile()
