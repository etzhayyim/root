from typing import TypedDict, Annotated, Sequence
from langgraph.graph import StateGraph, END
from langgraph.graph.message import add_messages

class SiliconState(TypedDict):
    purity_level: float
    certification_docs: Annotated[Sequence[str], add_messages]
    validation_status: bool

def validate_purity(state: SiliconState):
    is_valid = state['purity_level'] >= 99.9999
    return {'validation_status': is_valid}

def process_certification(state: SiliconState):
    # logic to cross-reference certification documents with registry
    return {'certification_docs': ['Verified Origin', 'ASTM Compliance Checked']}

graph = StateGraph(SiliconState)
graph.add_node('validate', validate_purity)
graph.add_node('certify', process_certification)
graph.set_entry_point('validate')
graph.add_edge('validate', 'certify')
graph.add_edge('certify', END)
graph = graph.compile()