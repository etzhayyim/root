from typing import TypedDict, Annotated, List
from langgraph.graph import StateGraph, END
import operator

class CommodityState(TypedDict):
    commodity_code: str
    quality_docs: List[str]
    validation_status: str
    risk_score: int

def validate_commodity(state: CommodityState):
    # Simulate inspection logic for agricultural raw materials
    return {'validation_status': 'passed' if len(state['quality_docs']) > 2 else 'failed'}

def assess_risk(state: CommodityState):
    return {'risk_score': 10 if state['validation_status'] == 'failed' else 2}

builder = StateGraph(CommodityState)
builder.add_node('validate', validate_commodity)
builder.add_node('risk', assess_risk)
builder.add_edge('validate', 'risk')
builder.add_edge('risk', END)
builder.set_entry_point('validate')
graph = builder.compile()
