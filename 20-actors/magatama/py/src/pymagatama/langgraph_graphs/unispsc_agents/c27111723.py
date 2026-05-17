from typing import TypedDict, Annotated
import operator
from langgraph.graph import StateGraph, END

class ToolState(TypedDict):
    tool_id: str
    material_certified: bool
    torque_tested: bool
    verification_logs: Annotated[list, operator.add]

def validate_material(state: ToolState):
    log = f'Verifying material grade for {state[\'tool_id\']}'
    return {'verification_logs': [log], 'material_certified': True}

def validate_torque(state: ToolState):
    log = f'Performing torque pressure check on {state[\'tool_id\']}'
    return {'verification_logs': [log], 'torque_tested': True}

graph = StateGraph(ToolState)
graph.add_node('material_check', validate_material)
graph.add_node('torque_check', validate_torque)
graph.set_entry_point('material_check')
graph.add_edge('material_check', 'torque_check')
graph.add_edge('torque_check', END)
graph = graph.compile()