from typing import TypedDict, List
from langgraph.graph import StateGraph, END

class FittingState(TypedDict):
    tool_list: List[str]
    validation_status: str
    is_compliant: bool

def validate_specs(state: FittingState):
    compliant = all([item.startswith('CERT-') for item in state['tool_list']])
    return {'validation_status': 'verified' if compliant else 'rejected', 'is_compliant': compliant}

def update_records(state: FittingState):
    print(f'Updating procurement logs for tools: {state['tool_list']}')
    return {'validation_status': 'recorded'}

graph = StateGraph(FittingState)
graph.add_node('validation', validate_specs)
graph.add_node('log', update_records)
graph.set_entry_point('validation')
graph.add_edge('validation', 'log')
graph.add_edge('log', END)
graph = graph.compile()