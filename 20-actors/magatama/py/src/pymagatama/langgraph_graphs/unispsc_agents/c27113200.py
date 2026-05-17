from langgraph.graph import StateGraph, END
from typing import TypedDict, List

class ToolKitState(TypedDict):
    tool_list: List[str]
    compliance_passed: bool
    validation_score: float

def validate_components(state: ToolKitState):
    required_tools = {'wrench', 'screwdriver', 'pliers'}
    found_tools = set(state['tool_list'])
    passing = required_tools.issubset(found_tools)
    return {'compliance_passed': passing, 'validation_score': 1.0 if passing else 0.0}

def finalize_kit(state: ToolKitState):
    print('Toolkit validated for procurement.')
    return {'validation_score': 1.0}

graph = StateGraph(ToolKitState)
graph.add_node('validation', validate_components)
graph.add_node('finalization', finalize_kit)
graph.set_entry_point('validation')
graph.add_edge('validation', 'finalization')
graph.add_edge('finalization', END)
graph = graph.compile()