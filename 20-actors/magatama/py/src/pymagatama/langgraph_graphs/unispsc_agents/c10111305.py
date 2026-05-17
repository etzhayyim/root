from typing import TypedDict, Annotated, Sequence
from langgraph.graph import StateGraph, END
import operator

class CattleFeedState(TypedDict):
    commodity_id: str
    nutrition_profile: dict
    validation_logs: Annotated[Sequence[str], operator.add]
    is_compliant: bool

def validate_nutrition(state: CattleFeedState):
    profile = state['nutrition_profile']
    valid = profile.get('protein', 0) > 10
    return {'validation_logs': ['Nutrition validated'], 'is_compliant': valid}

def process_batch(state: CattleFeedState):
    return {'validation_logs': ['Batch processed and logged']}

builder = StateGraph(CattleFeedState)
builder.add_node('validate', validate_nutrition)
builder.add_node('process', process_batch)
builder.add_edge('validate', 'process')
builder.add_edge('process', END)
builder.set_entry_point('validate')
graph = builder.compile()