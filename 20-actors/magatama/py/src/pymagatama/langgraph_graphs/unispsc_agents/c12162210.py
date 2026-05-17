from typing import TypedDict, Annotated, Sequence
import operator
from langgraph.graph import StateGraph, END

class FluorineState(TypedDict):
    purity_level: float
    safety_clearance: bool
    log: Annotated[Sequence[str], operator.add]

def validate_purity(state: FluorineState) -> FluorineState:
    if state['purity_level'] < 99.999:
        return {'log': ['Purity check failed: Below 5N threshold.']}
    return {'log': ['Purity validated successfully.']}

def safety_routing(state: FluorineState) -> str:
    return 'safe' if state['safety_clearance'] else 'halt'

def process_shipment(state: FluorineState) -> FluorineState:
    return {'log': ['Processing hazardous material shipment protocols.']}

def halt_process(state: FluorineState) -> FluorineState:
    return {'log': ['ABORT: High-purity fluorine safety violation.']}

graph = StateGraph(FluorineState)
graph.add_node('validate', validate_purity)
graph.add_node('process', process_shipment)
graph.add_node('halt', halt_process)
graph.add_edge('validate', 'process')
graph.add_conditional_edges('validate', safety_routing, {'safe': 'process', 'halt': 'halt'})
graph.add_edge('process', END)
graph.add_edge('halt', END)
graph.set_entry_point('validate')
graph = graph.compile()