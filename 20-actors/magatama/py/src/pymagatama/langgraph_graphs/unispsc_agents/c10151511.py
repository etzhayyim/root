from typing import TypedDict, Annotated, List
from langgraph.graph import StateGraph, END
import operator

class CommodityState(TypedDict):
    commodity_id: str
    quality_score: float
    inspection_passed: bool
    traceability_logs: Annotated[List[str], operator.add]

def validate_quality(state: CommodityState) -> CommodityState:
    # Mock quality logic
    score = 0.95
    return {'quality_score': score, 'inspection_passed': score > 0.8}

def update_logs(state: CommodityState) -> CommodityState:
    log = f'Processed at {state.commodity_id}: status={state.inspection_passed}'
    return {'traceability_logs': [log]}

workflow = StateGraph(CommodityState)
workflow.add_node('validate', validate_quality)
workflow.add_node('log', update_logs)
workflow.set_entry_point('validate')
workflow.add_edge('validate', 'log')
workflow.add_edge('log', END)
graph = workflow.compile()
