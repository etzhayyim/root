from typing import TypedDict, Annotated, Sequence
from langgraph.graph import StateGraph, END
import operator

class OilProcurementState(TypedDict):
    commodity_code: str
    specifications: dict
    validation_log: Annotated[Sequence[str], operator.add]
    is_compliant: bool

def validate_purity(state: OilProcurementState):
    purity = state['specifications'].get('purity_percentage', 0)
    if purity >= 99.0:
        return {'validation_log': ['Purity level acceptable'], 'is_compliant': True}
    return {'validation_log': ['Purity too low'], 'is_compliant': False}

def safety_check(state: OilProcurementState):
    flash_point = state['specifications'].get('flash_point_celsius', 0)
    if flash_point > 100:
        return {'validation_log': ['Safety standards met']}
    return {'validation_log': ['High risk: Flash point below threshold']}

graph = StateGraph(OilProcurementState)
graph.add_node('validate_purity', validate_purity)
graph.add_node('safety_check', safety_check)
graph.set_entry_point('validate_purity')
graph.add_edge('validate_purity', 'safety_check')
graph.add_edge('safety_check', END)

compiled_graph = graph.compile()