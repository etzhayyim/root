from typing import TypedDict, Annotated
from langgraph.graph import StateGraph, END

class ToolState(TypedDict):
    tool_type: str
    spec_data: dict
    is_validated: bool

def validate_tool_specs(state: ToolState):
    hardness = state['spec_data'].get('hardness', 0)
    if hardness >= 45:
        return {**state, 'is_validated': True}
    return {**state, 'is_validated': False}

def process_procurement(state: ToolState):
    print(f'Processing procurement for {state['tool_type']}')
    return {'is_validated': state['is_validated']}

workflow = StateGraph(ToolState)
workflow.add_node('validate', validate_tool_specs)
workflow.add_node('procure', process_procurement)
workflow.set_entry_point('validate')
workflow.add_edge('validate', 'procure')
workflow.add_edge('procure', END)
graph = workflow.compile()
