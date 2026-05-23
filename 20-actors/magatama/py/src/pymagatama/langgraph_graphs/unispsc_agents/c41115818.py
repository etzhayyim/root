from typing import TypedDict, List
from langgraph.graph import StateGraph, END

class HistologyState(TypedDict):
    item_id: str
    quality_docs: List[str]
    storage_temp: float
    status: str

def validate_certification(state: HistologyState):
    if 'ISO_13485' in state['quality_docs']:
        return {'status': 'CERTIFIED'}
    return {'status': 'REJECTED'}

def check_temp(state: HistologyState):
    if state['storage_temp'] < 25.0:
        return {'status': 'APPROVED'}
    return {'status': 'CRITICAL_REFRIGERATION_REQUIRED'}

graph = StateGraph(HistologyState)
graph.add_node('validate_cert', validate_certification)
graph.add_node('verify_temp', check_temp)
graph.set_entry_point('validate_cert')
graph.add_edge('validate_cert', 'verify_temp')
graph.add_edge('verify_temp', END)

graph = graph.compile()
