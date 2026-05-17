from typing import TypedDict
from langgraph.graph import StateGraph, END

class LatticeModelState(TypedDict):
    model_type: str
    material_spec: str
    verification_passed: bool

def validate_model(state: LatticeModelState):
    state['verification_passed'] = 'plastic' in state['material_spec'].lower() or 'metal' in state['material_spec'].lower()
    return state

def assembly_process(state: LatticeModelState):
    print(f'Processing crystal model: {state.get("model_type")}')
    return state

graph = StateGraph(LatticeModelState)
graph.add_node('validate', validate_model)
graph.add_node('assemble', assembly_process)
graph.set_entry_point('validate')
graph.add_edge('validate', 'assemble')
graph.add_edge('assemble', END)
app = graph.compile()