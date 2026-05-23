from langgraph.graph import StateGraph, END
from typing import TypedDict, List

class ToolSpec(TypedDict):
    tool_id: str
    material_spec: str
    qc_passed: bool

class State(TypedDict):
    data: ToolSpec

def validate_tool(state: State) -> State:
    # Logic to verify etching needle specifications
    if state['data']['material_spec']:
        state['data']['qc_passed'] = True
    return state

def finalize_spec(state: State) -> State:
    print(f'Finalizing spec for needle: {state['data']['tool_id']}')
    return state

graph = StateGraph(State)
graph.add_node('validate', validate_tool)
graph.add_node('finalize', finalize_spec)
graph.set_entry_point('validate')
graph.add_edge('validate', 'finalize')
graph.add_edge('finalize', END)
graph = graph.compile()
