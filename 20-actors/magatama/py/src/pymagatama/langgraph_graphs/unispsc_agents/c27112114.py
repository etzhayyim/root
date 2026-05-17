from typing import TypedDict
from langgraph.graph import StateGraph, END

class ToolSpecState(TypedDict):
    tool_name: str
    hrc_rating: int
    is_insulated: bool
    validation_status: str

def validate_hardness(state: ToolSpecState):
    if state['hrc_rating'] < 55:
        return {'validation_status': 'REJECTED: Below required hardness'}
    return {'validation_status': 'PASSED'}

def check_insulation(state: ToolSpecState):
    if state['is_insulated']:
        return {'validation_status': 'PASSED: VDE Certified'}
    return {'validation_status': 'PASSED: Standard Industrial'}

graph = StateGraph(ToolSpecState)
graph.add_node('hardness_check', validate_hardness)
graph.add_node('insulation_check', check_insulation)
graph.set_entry_point('hardness_check')
graph.add_edge('hardness_check', 'insulation_check')
graph.add_edge('insulation_check', END)
graph = graph.compile()