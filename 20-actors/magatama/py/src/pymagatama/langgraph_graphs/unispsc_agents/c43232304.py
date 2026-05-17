from typing import TypedDict
from langgraph.graph import StateGraph, END

class DBState(TypedDict):
    db_type: str
    compliance_tags: list
    is_approved: bool

def validate_db_security(state: DBState):
    state['is_approved'] = 'encryption' in state.get('compliance_tags', [])
    return state

def route_by_type(state: DBState):
    return 'process_rdbms' if state['db_type'] == 'RDBMS' else 'process_nosql'

graph = StateGraph(DBState)
graph.add_node('validate', validate_db_security)
graph.add_node('process_rdbms', lambda s: s)
graph.add_node('process_nosql', lambda s: s)
graph.set_entry_point('validate')
graph.add_conditional_edges('validate', route_by_type)
graph.add_edge('process_rdbms', END)
graph.add_edge('process_nosql', END)
graph = graph.compile()