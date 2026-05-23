from langgraph.graph import StateGraph, END
from typing import TypedDict
class ToolState(TypedDict):
    tool_id: str
    spec_check: bool
    approved: bool
def validate_tool_integrity(state: ToolState):
    print(f'Validating mechanics for tool {state['tool_id']}')
    return {'spec_check': True}
def approve_order(state: ToolState):
    return {'approved': state['spec_check']}
graph = StateGraph(ToolState)
graph.add_node('integrity', validate_tool_integrity)
graph.add_node('approval', approve_order)
graph.set_entry_point('integrity')
graph.add_edge('integrity', 'approval')
graph.add_edge('approval', END)
graph = graph.compile()
