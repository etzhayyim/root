import * as fs from 'fs';
import * as readline from 'readline';
import { Etzhayyim, signal } from '@etzhayyim/sdk';

export interface NDJSONRecord {
  v: number;
  ts: number;
  actorDid: string;
  code?: string;
  title?: string;
  mood?: string;
  contentSourceKind?: string;
  text?: string;
  lexicon: string;
  createdAt: string;
  recipientDid?: string;
  encryptedPayload?: string;
}

export class OrganismPostDrainer {
  private queuePath: string;
  private pdsUrl: string;

  constructor(queuePath: string, pdsUrl: string) {
    this.queuePath = queuePath;
    this.pdsUrl = pdsUrl;
  }

  public async processLine(line: string): Promise<void> {
    if (!line.trim()) return;

    let record: NDJSONRecord;
    try {
      record = JSON.parse(line) as NDJSONRecord;
    } catch (e) {
      console.error("Failed to parse line:", line);
      return;
    }

    if (record.v !== 1) {
      console.warn(`Unsupported schema version: ${record.v}`);
      return;
    }

    if (record.lexicon === "app.bsky.feed.post") {
      await this.dispatchPost(record);
    } else if (record.lexicon === "app.etzhayyim.organism.message") {
      const encrypted = await this.encryptMessage(record);
      await this.dispatchMessage(encrypted);
    } else {
      console.warn(`Unknown lexicon: ${record.lexicon}`);
    }
  }

  private async encryptMessage(record: NDJSONRecord): Promise<NDJSONRecord> {
    if (record.encryptedPayload) return record;
    if (!record.text || !record.recipientDid) {
      console.warn("[Drainer] Message missing text or recipientDid, cannot encrypt");
      return record;
    }

    console.log(`[Drainer] Encrypting message from ${record.actorDid} to ${record.recipientDid} via Signal keywrap`);

    // Per ADR-2605266000 & 2605181100:
    // This is a minimal mock encryption layer implementing Wave 3.2.
    // In full implementation, it uses @etzhayyim/sdk/signal (libsignal-client):
    // const session = await signal.establishSession({ ... });
    // const wrap = await signal.wrapKey({ session, ... });

    const mockPlaintext = record.text;
    const mockCiphertext = Buffer.from(mockPlaintext).toString("base64");

    return {
      ...record,
      encryptedPayload: `mock-signal-keywrap-v1(${mockCiphertext})`
    };
  }

  private async dispatchPost(record: NDJSONRecord): Promise<void> {
    console.log(`[Drainer] Dispatching post for ${record.actorDid} to ${this.pdsUrl}`);
    const sdk = new Etzhayyim({ did: record.actorDid, pdsUrl: this.pdsUrl });
    // Note: mock write for now unless sdk.write is actually implemented
    await (sdk as any).write({
      collection: "app.bsky.feed.post",
      record: {
        text: record.text,
        createdAt: record.createdAt,
      }
    });
  }

  private async dispatchMessage(record: NDJSONRecord): Promise<void> {
    console.log(`[Drainer] Dispatching message from ${record.actorDid} to ${record.recipientDid}`);
    const sdk = new Etzhayyim({ did: record.actorDid, pdsUrl: this.pdsUrl });
    await (sdk as any).write({
      collection: "app.etzhayyim.organism.message",
      record: {
        recipientDid: record.recipientDid,
        senderDid: record.actorDid,
        encryptedPayload: record.encryptedPayload,
        createdAt: record.createdAt,
      }
    });
  }

  public async start(): Promise<void> {
    if (!fs.existsSync(this.queuePath)) {
      console.error(`Queue file not found: ${this.queuePath}`);
      return;
    }

    console.log(`Starting drainer tailing ${this.queuePath} to ${this.pdsUrl}`);
    // Simple mock tailer - in production, we would use something like `tail` package or fs.watch
    const fileStream = fs.createReadStream(this.queuePath);
    const rl = readline.createInterface({
      input: fileStream,
      crlfDelay: Infinity,
    });

    for await (const line of rl) {
      await this.processLine(line);
    }
  }
}

export function main() {
  const queuePath = process.env.ORGANISM_POST_QUEUE_PATH;
  const pdsUrl = process.env.ETZHAYYIM_PDS_URL;

  if (!queuePath || !pdsUrl) {
    console.error("Missing required env vars: ORGANISM_POST_QUEUE_PATH, ETZHAYYIM_PDS_URL");
    process.exit(1);
  }

  const drainer = new OrganismPostDrainer(queuePath, pdsUrl);
  drainer.start().catch(console.error);
}

if (require.main === module) {
  main();
}
