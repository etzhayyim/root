from typing import TypedDict, Annotated, Sequence
import operator
from langgraph.graph import StateGraph, END

class GatewayState(TypedDict):
    config_payload: dict
    validation_logs: Annotated[Sequence[str], operator.add]
    is_compliant: bool

def validate_network_specs(state: GatewayState):
    config = state['config_payload']
    logs = [f'Checking throughput: {config.get("throughput_gbps")} Gbps']
    compliant = config.get("throughput_gbps", 0) >= 10
    return {'validation_logs': logs, 'is_compliant': compliant}

def deploy_gateway(state: GatewayState):
    return {'validation_logs': ['Gateway deployed successfully']}

graph = StateGraph(GatewayState)
graph.add_node('validate', validate_network_specs)
graph.add_node('deploy', deploy_gateway)
graph.add_edge('validate', 'deploy')
graph.add_edge('deploy', END)
graph.set_entry_point('validate')
graph = graph.compile()