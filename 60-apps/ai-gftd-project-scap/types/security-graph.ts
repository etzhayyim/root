export interface GraphNode {
  id: string;
  type: string;
  label: string;
  hasWarning?: boolean;
}

export interface GraphEdge {
  source: string;
  target: string;
  label?: string;
}

type ResourceCreatedEvent = {
  type: "RESOURCE_CREATED";
  payload: {
    id: string;
    type: string;
    label: string;
  };
};

type PolicyAttachedEvent = {
  type: "POLICY_ATTACHED";
  payload: {
    source: string;
    target: string;
    policy: string;
  };
};

type VulnerabilityFoundEvent = {
  type: "VULNERABILITY_FOUND";
  payload: {
    resourceId: string;
    vulnerabilityId: string;
    description: string;
  };
};

type ConnectionEstablishedEvent = {
  type: "CONNECTION_ESTABLISHED";
  payload: {
    source: string;
    target: string;
    port: string | number;
  };
};

export type SecurityEvent =
  | ResourceCreatedEvent
  | PolicyAttachedEvent
  | VulnerabilityFoundEvent
  | ConnectionEstablishedEvent;
