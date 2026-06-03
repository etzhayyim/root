import { describe, it, expect } from 'vitest';
import type {
	ConvoEnvelope, Convo, ConvoMember, PresenceState,
	StreamEvent, ConvoEntry, ConvoGroup,
	SyncState, WDiff, CallSignal,
	ConvoParticipantType, ConversationKind,
} from '$lib/atproto-agent';

describe('AT Protocol types', () => {
	it('ConvoEnvelope can represent a plaintext message', () => {
		const env: ConvoEnvelope = {
			id: '01TEST',
			kind: 'message',
			recordCid:'abc123',
			atUri: 'at://did:plc:alice/com.etzhayyim.w.message/tid1',
			rkey: 'tid1',
			senderDid: 'did:plc:alice',
			orgId: 'org1',
			convoId: 'cv1',
			threadId: '',
			replyTo: '',
			payload: btoa('hello world'),
			contentType: 'text/plain',
			encryption: 'plaintext',
			causationId: '',
			correlationId: '',
			createdAt: '2026-03-19T00:00:00Z',
		};
		expect(env.id).toBe('01TEST');
		expect(env.encryption).toBe('plaintext');
		expect(atob(env.payload)).toBe('hello world');
	});

	it('ConvoEnvelope supports Signal encryption states', () => {
		const states: ConvoEnvelope['encryption'][] = ['plaintext', 'signal-1to1', 'signal-group', 'client-encrypted'];
		expect(states).toHaveLength(4);
	});

	it('Convo includes conversationKind', () => {
		const ch: Convo = {
			convoId: 'cvDm1',
			orgId: 'org1',
			name: 'DM',
			description: '',
			kind: 'direct',
			encryptionMode: 'signal-1to1',
			creatorDid: 'did:plc:alice',
			memberCount: 2,
			atUri: '',
						createdAt: '2026-03-19T00:00:00Z',
			conversationKind: 'user2user',
		};
		expect(ch.conversationKind).toBe('user2user');
	});

	it('Convo kind covers all supported types', () => {
		const kinds: Convo['kind'][] = ['public', 'private', 'direct', 'group-dm', 'bot', 'space', 'email'];
		expect(kinds).toHaveLength(7);
	});

	it('ConvoMember includes participantType', () => {
		const member: ConvoMember = {
			convoId: 'cv1',
			did: 'did:plc:bob',
			role: 'member',
			joinedAt: '2026-03-19T00:00:00Z',
			participantType: 'agent',
		};
		expect(member.participantType).toBe('agent');
	});

	it('ConvoParticipantType covers human/agent/service', () => {
		const types: ConvoParticipantType[] = ['human', 'agent', 'service'];
		expect(types).toHaveLength(3);
	});

	it('ConversationKind covers all 3 patterns', () => {
		const kinds: ConversationKind[] = ['user2user', 'user2agent', 'agent2agent'];
		expect(kinds).toHaveLength(3);
	});

	it('PresenceState represents online status', () => {
		const p: PresenceState = {
			did: 'did:plc:alice',
			status: 'online',
			statusText: 'Working',
			lastActive: '2026-03-19T12:00:00Z',
		};
		expect(p.status).toBe('online');
	});

	it('StreamEvent represents a create action', () => {
		const ev: StreamEvent = {
			action: 'create',
			convoId: 'cv1',
			envelope: {
				id: 'e1', kind: 'message', recordCid:'', atUri: '', rkey: 'r1',
				senderDid: 'did:plc:alice', orgId: 'org1', convoId: 'cv1',
				threadId: '', replyTo: '', payload: '', contentType: 'text/plain',
				encryption: 'plaintext', causationId: '', correlationId: '',
				createdAt: '2026-03-19T00:00:00Z',
			},
		};
		expect(ev.action).toBe('create');
		expect(ev.envelope!.senderDid).toBe('did:plc:alice');
	});

	it('ConvoGroup sections match expected values', () => {
		const group: ConvoGroup = {
			section: 'favorites',
			label: 'Favorites',
			convos: [],
		};
		expect(group.section).toBe('favorites');
	});

	it('SyncState represents convo sync anchor', () => {
		const sync: SyncState = {
			convoId: 'cv1',
			rootCid: 'abc123',
			version: 42,
			timestampNs: '1710700800000000000',
		};
		expect(sync.version).toBe(42);
	});

	it('WDiff tracks added/removed changes', () => {
		const diff: WDiff = {
			addedEnvelopeCids: ['cid1', 'cid2'],
			removedEnvelopeCids: [],
			addedMemberCids: ['m1'],
			removedMemberCids: [],
			addedKinds: ['reaction'],
			removedKinds: [],
			channelChanged: false,
		};
		expect(diff.addedEnvelopeCids).toHaveLength(2);
		expect(diff.addedKinds).toContain('reaction');
	});

	it('CallSignal represents an offer', () => {
		const signal: CallSignal = {
			type: 'offer',
			callId: 'call1',
			convoId: 'cv1',
			sdp: 'v=0...',
			mediaType: 'audio',
		};
		expect(signal.type).toBe('offer');
	});
});

describe('conversation kind mapping', () => {
	it('Direct convo maps to user2user', () => {
		const ch: Convo = {
			convoId: 'dm1', orgId: 'org', name: 'DM', description: '',
			kind: 'direct', encryptionMode: 'signal-1to1', creatorDid: 'did:plc:a',
			memberCount: 2, atUri: '', mdagRootCid: '', createdAt: '',
			conversationKind: 'user2user',
		};
		expect(ch.conversationKind).toBe('user2user');
	});

	it('Bot convo maps to user2agent', () => {
		const ch: Convo = {
			convoId: 'bot1', orgId: 'org', name: 'Bot', description: '',
			kind: 'bot', encryptionMode: 'signal-1to1', creatorDid: 'did:plc:a',
			memberCount: 2, atUri: '', mdagRootCid: '', createdAt: '',
			conversationKind: 'user2agent',
		};
		expect(ch.conversationKind).toBe('user2agent');
	});

	it('Public convo has no conversationKind', () => {
		const ch: Convo = {
			convoId: 'pub1', orgId: 'org', name: 'General', description: '',
			kind: 'public', encryptionMode: 'plaintext', creatorDid: 'did:plc:a',
			memberCount: 100, atUri: '', mdagRootCid: '', createdAt: '',
		};
		expect(ch.conversationKind).toBeUndefined();
	});
});
