from typing import TypedDict, Annotated, Sequence
import operator
from langgraph.graph import StateGraph, END

class BridgeState(TypedDict):
    config: dict
    validation_results: Annotated[list, operator.add]
    is_approved: bool

def validate_throughput(state: BridgeState):
    config = state['config']
    result = {'valid': config.get('throughput_bps', 0) > 1000, 'msg': 'Throughput check'}
    return {'validation_results': [result]}

def finalize_check(state: BridgeState):
    is_valid = all(r['valid'] for r in state['validation_results'])
    return {'is_approved': is_valid}

graph = StateGraph(BridgeState)
graph.add_node('validate', validate_throughput)
graph.add_node('finalize', finalize_check)
graph.set_entry_point('validate')
graph.add_edge('validate', 'finalize')
graph.add_edge('finalize', END)
graph = graph.compile()
