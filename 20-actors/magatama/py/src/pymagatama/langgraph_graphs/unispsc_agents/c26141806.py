from typing import TypedDict, List
from langgraph.graph import StateGraph, END

class HotCellState(TypedDict):
    tool_id: str
    radiation_rating: float
    safety_clearance: bool
    validation_logs: List[str]

def validate_tool_specs(state: HotCellState):
    if state['radiation_rating'] > 1000:
        return {'validation_logs': ['Radiation resistance validated for high-level use']}
    return {'validation_logs': ['Warning: Radiation threshold below standard']}

def check_compliance(state: HotCellState):
    state['safety_clearance'] = True
    return state

graph = StateGraph(HotCellState)
graph.add_node('validate', validate_tool_specs)
graph.add_node('compliance', check_compliance)
graph.add_edge('validate', 'compliance')
graph.add_edge('compliance', END)
graph.set_entry_point('validate')
graph = graph.compile()
