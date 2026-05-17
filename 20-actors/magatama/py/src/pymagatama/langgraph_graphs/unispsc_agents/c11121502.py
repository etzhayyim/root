from typing import TypedDict, List, Annotated
import operator
from langgraph.graph import StateGraph, END

class MetallurgicalState(TypedDict):
    purity: float
    batch_id: str
    validation_log: Annotated[List[str], operator.add]
    is_cleared: bool

def validate_purity(state: MetallurgicalState) -> MetallurgicalState:
    min_purity = 99.9
    status = state['purity'] >= min_purity
    return {"is_cleared": status, "validation_log": [f"Purity check: {state['purity']} - {'Passed' if status else 'Failed'}"]}

def update_records(state: MetallurgicalState) -> MetallurgicalState:
    if not state['is_cleared']:
        return {"validation_log": ["HALTED: Purity below threshold for batch record update"]}
    return {"validation_log": [f"Batch {state['batch_id']} successfully logged to registry."]}

graph = StateGraph(MetallurgicalState)
graph.add_node("validate", validate_purity)
graph.add_node("record", update_records)
graph.add_edge("validate", "record")
graph.add_edge("record", END)
graph.set_entry_point("validate")
graph = graph.compile()