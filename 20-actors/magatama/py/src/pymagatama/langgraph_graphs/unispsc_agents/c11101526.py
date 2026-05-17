from typing import TypedDict, Annotated, Sequence
from langgraph.graph import StateGraph, END
from langgraph.graph.message import add_messages

class MineralState(TypedDict):
    purity: float
    particle_size: str
    validation_log: Annotated[Sequence[str], add_messages]

def validate_purity(state: MineralState):
    is_valid = state['purity'] >= 99.0
    return {'validation_log': [f'Purity check: {state["purity"]}%, Status: {"PASS" if is_valid else "FAIL"}']}

def check_size(state: MineralState):
    return {'validation_log': [f'Particle size check: {state["particle_size"]}, Status: APPROVED']}

graph = StateGraph(MineralState)
graph.add_node('validate_purity', validate_purity)
graph.add_node('check_size', check_size)
graph.set_entry_point('validate_purity')
graph.add_edge('validate_purity', 'check_size')
graph.add_edge('check_size', END)
graph = graph.compile()