from typing import TypedDict, List
from langgraph.graph import StateGraph, END

class MandarinJuiceState(TypedDict):
    batch_id: str
    quality_docs: List[str]
    passed_qc: bool

def validate_quality(state: MandarinJuiceState):
    required = ['brix_report', 'pesticide_test']
    passed = all(doc in state['quality_docs'] for doc in required)
    return {'passed_qc': passed}

graph_builder = StateGraph(MandarinJuiceState)
graph_builder.add_node('qc_check', validate_quality)
graph_builder.set_entry_point('qc_check')
graph_builder.add_edge('qc_check', END)
graph = graph_builder.compile()