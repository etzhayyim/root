from typing import TypedDict, List
from langgraph.graph import StateGraph, END

class ToolProcessState(TypedDict):
    tool_list: List[str]
    validation_errors: List[str]
    is_compliant: bool

def validate_tools(state: ToolProcessState):
    errors = []
    for tool in state['tool_list']:
        if 'power' in tool.lower() and 'safety_cert' not in state:
            errors.append(f'Tool {tool} requires safety certification')
    return {'validation_errors': errors, 'is_compliant': len(errors) == 0}

graph = StateGraph(ToolProcessState)
graph.add_node('validate', validate_tools)
graph.set_entry_point('validate')
graph.add_edge('validate', END)
app = graph.compile()
