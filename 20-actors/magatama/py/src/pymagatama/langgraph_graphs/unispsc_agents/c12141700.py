from typing import TypedDict, Annotated, List
from langgraph.graph import StateGraph, END
import operator

class WaferState(TypedDict):
    purity: float
    diameter: int
    inspected: bool
    validation_log: Annotated[List[str], operator.add]

def validate_wafer_specs(state: WaferState):
    if state['purity'] >= 99.9999 and state['diameter'] >= 300:
        return {'inspected': True, 'validation_log': ['High-spec wafer verified']}
    return {'inspected': False, 'validation_log': ['Failed specification validation']}

def route_by_inspection(state: WaferState):
    return 'process' if state['inspected'] else END

def process_wafer(state: WaferState):
    return {'validation_log': ['Entering cleanroom fabrication workflow']}

graph = StateGraph(WaferState)
graph.add_node('validate', validate_wafer_specs)
graph.add_node('process', process_wafer)
graph.set_entry_point('validate')
graph.add_conditional_edges('validate', route_by_inspection)
graph.add_edge('process', END)
graph = graph.compile()
