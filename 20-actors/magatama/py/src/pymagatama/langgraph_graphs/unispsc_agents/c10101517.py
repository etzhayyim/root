from typing import TypedDict, Annotated, Sequence
from langgraph.graph import StateGraph, END
from langgraph.graph.message import add_messages

class MiningState(TypedDict):
    task_id: str
    specification: dict
    validation_log: Annotated[Sequence[str], add_messages]

def validate_drill_spec(state: MiningState):
    spec = state['specification']
    log = []
    if spec.get('hardness_rating', 0) < 50:
        log.append('Error: Hardness rating below industrial standard.')
    else:
        log.append('Drill bit specification validated for mining usage.')
    return {'validation_log': log}

def deploy_inspection_node(state: MiningState):
    log = ['Initiating physical inspection protocol for geological tools.']
    return {'validation_log': log}

graph = StateGraph(MiningState)
graph.add_node('validate', validate_drill_spec)
graph.add_node('inspect', deploy_inspection_node)
graph.add_edge('validate', 'inspect')
graph.add_edge('inspect', END)
graph.set_entry_point('validate')
graph = graph.compile()