from typing import TypedDict, Annotated, Sequence
import operator
from langgraph.graph import StateGraph, END

class IndustrialProcurementState(TypedDict):
    commodity_id: str
    specs: dict
    validation_log: Annotated[Sequence[str], operator.add]
    status: str

def validate_specs(state: IndustrialProcurementState):
    log = []
    if 'manufacturer_certification' not in state['specs']:
        log.append('Missing mandatory certification.')
    return {'validation_log': log}

def route_to_engineering(state: IndustrialProcurementState):
    return 'engineering_review' if 'high_value' in state.get('tags', []) else END

graph = StateGraph(IndustrialProcurementState)
graph.add_node('validate', validate_specs)
graph.add_edge('validate', END)
graph.set_entry_point('validate')
graph = graph.compile()