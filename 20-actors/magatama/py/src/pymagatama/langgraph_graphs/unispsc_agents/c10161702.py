from typing import TypedDict, Annotated, List
from langgraph.graph import StateGraph, END
import operator

class CommodityState(TypedDict):
    commodity_id: str
    spec_data: dict
    validation_log: Annotated[List[str], operator.add]
    is_approved: bool

def validate_origin(state: CommodityState):
    origin = state['spec_data'].get('origin_country')
    if origin:
        return {'validation_log': [f'Origin {origin} verified.']}
    return {'validation_log': ['Origin missing.']}

def check_certification(state: CommodityState):
    cert = state['spec_data'].get('certification_standard')
    status = True if cert else False
    return {'is_approved': status, 'validation_log': [f'Certification check: {status}']}

graph = StateGraph(CommodityState)
graph.add_node('validate_origin', validate_origin)
graph.add_node('check_certification', check_certification)
graph.set_entry_point('validate_origin')
graph.add_edge('validate_origin', 'check_certification')
graph.add_edge('check_certification', END)
graph = graph.compile()