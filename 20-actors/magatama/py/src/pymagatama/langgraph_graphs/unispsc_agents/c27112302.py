from typing import TypedDict
from langgraph.graph import StateGraph, END

class AwlState(TypedDict):
    spec_data: dict
    is_validated: bool
    error_log: list

def validate_awl(state: AwlState):
    hardness = state['spec_data'].get('tip_hardness_hrc', 0)
    valid = 50 <= hardness <= 65
    return {'is_validated': valid, 'error_log': [] if valid else ['Invalid hardness range']}

graph = StateGraph(AwlState)
graph.add_node('validate', validate_awl)
graph.set_entry_point('validate')
graph.add_edge('validate', END)
graph = graph.compile()
