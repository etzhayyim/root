from typing import TypedDict, Annotated, Sequence
import operator
from langgraph.graph import StateGraph, END

class CassetteDeviceState(TypedDict):
    specs: dict
    validation_results: Annotated[Sequence[str], operator.add]
    status: str

def validate_audio_specs(state: CassetteDeviceState):
    specs = state['specs']
    log = []
    if 'frequency_response' not in specs: log.append('Missing frequency response')
    if 'sn_ratio' not in specs: log.append('Missing SNR rating')
    return {'validation_results': log, 'status': 'validated' if not log else 'failed'}

def route_by_status(state: CassetteDeviceState):
    return 'success' if state['status'] == 'validated' else 'fail'

graph = StateGraph(CassetteDeviceState)
graph.add_node('validate', validate_audio_specs)
graph.set_entry_point('validate')
graph.add_edge('validate', END)
graph.compile()