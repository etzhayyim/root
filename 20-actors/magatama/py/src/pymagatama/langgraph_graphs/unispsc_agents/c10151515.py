from typing import TypedDict, Annotated, List
from langgraph.graph import StateGraph, END

class FeedState(TypedDict):
    ingredient_list: List[str]
    validation_report: str
    is_compliant: bool

def validate_ingredients(state: FeedState):
    # Simple logic to check if ingredients are approved
    compliant = all(len(i) > 3 for i in state['ingredient_list'])
    return {'is_compliant': compliant, 'validation_report': 'Validated' if compliant else 'Failed'}

def finish(state: FeedState):
    return {'validation_report': state['validation_report']}

graph = StateGraph(FeedState)
graph.add_node('validate', validate_ingredients)
graph.add_node('finish', finish)
graph.add_edge('validate', 'finish')
graph.add_edge('finish', END)
graph.set_entry_point('validate')
graph = graph.compile()
