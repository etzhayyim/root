from typing import TypedDict, Annotated, Sequence
import operator
from langgraph.graph import StateGraph, END

class FeedState(TypedDict):
    commodity_id: str
    quality_metrics: dict
    workflow_steps: Annotated[Sequence[str], operator.add]

def validate_metrics(state: FeedState) -> dict:
    is_valid = state['quality_metrics'].get('moisture', 0) < 14.0
    return {'workflow_steps': ['Validation' if is_valid else 'Rejection']}

def process_procurement(state: FeedState) -> dict:
    return {'workflow_steps': ['Procurement Initiated']}

builder = StateGraph(FeedState)
builder.add_node('validate', validate_metrics)
builder.add_node('procure', process_procurement)
builder.set_entry_point('validate')
builder.add_edge('validate', 'procure')
builder.add_edge('procure', END)
graph = builder.compile()