from typing import TypedDict, Annotated
from langgraph.graph import StateGraph, END

class ToolProcessState(TypedDict):
    tool_id: str
    material_hardness: float
    inspection_passed: bool
    validation_log: list[str]

def validate_material_compatibility(state: ToolProcessState) -> ToolProcessState:
    if state['material_hardness'] > 8.0:
        state['validation_log'].append('Hardness within operational limits.')
        state['inspection_passed'] = True
    else:
        state['validation_log'].append('Material too soft for diamond tooling.')
        state['inspection_passed'] = False
    return state

def execute_grinding_simulation(state: ToolProcessState) -> ToolProcessState:
    if state['inspection_passed']:
        state['validation_log'].append('Grinding simulation successful.')
    return state

graph = StateGraph(ToolProcessState)
graph.add_node('validate', validate_material_compatibility)
graph.add_node('grind', execute_grinding_simulation)
graph.add_edge('validate', 'grind')
graph.add_edge('grind', END)
graph.set_entry_point('validate')
graph = graph.compile()
