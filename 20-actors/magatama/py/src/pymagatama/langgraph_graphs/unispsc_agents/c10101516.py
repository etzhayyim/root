from typing import TypedDict, Annotated, Sequence
import operator
from langgraph.graph import StateGraph, END

class HayState(TypedDict):
    hay_data: dict
    validation_logs: Annotated[Sequence[str], operator.add]
    is_approved: bool

def validate_moisture(state: HayState) -> HayState:
    moisture = state['hay_data'].get('moisture_percentage', 0)
    if moisture > 15:
        return {'validation_logs': ['Moisture level too high for storage'], 'is_approved': False}
    return {'validation_logs': ['Moisture level compliant'], 'is_approved': True}

def check_phytosanitary(state: HayState) -> HayState:
    if not state['hay_data'].get('phytosanitary_certificate'):
        return {'validation_logs': ['Missing phytosanitary certificate'], 'is_approved': False}
    return {'validation_logs': ['Certificate verified'], 'is_approved': True}

graph = StateGraph(HayState)
graph.add_node('check_moisture', validate_moisture)
graph.add_node('check_cert', check_phytosanitary)
graph.set_entry_point('check_moisture')
graph.add_edge('check_moisture', 'check_cert')
graph.add_edge('check_cert', END)
graph = graph.compile()
