import * as fs from 'fs';
import * as readline from 'readline';

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
    } else if (record.lexicon === "app.etzhayyim.apps.etzhayyim.message") {
      await this.dispatchMessage(record);
    } else {
      console.warn(`Unknown lexicon: ${record.lexicon}`);
    }
  }

  private async dispatchPost(record: NDJSONRecord): Promise<void> {
    console.log(`[Drainer] Dispatching post for ${record.actorDid} to ${this.pdsUrl}`);
    // Minimal integration hook for @etzhayyim/sdk
    // sdk.pds.dispatch({
    //   type: "app.bsky.feed.post",
    //   actorDid: record.actorDid,
    //   text: record.text,
    //   createdAt: record.createdAt,
    // });
  }

  private async dispatchMessage(record: NDJSONRecord): Promise<void> {
    console.log(`[Drainer] Dispatching message from ${record.actorDid} to ${record.recipientDid}`);
    // Future: Signal keywrap encryption and envelope creation (ADR-2605266000)
    // sdk.pds.dispatch({
    //   type: "app.etzhayyim.apps.etzhayyim.message",
    //   recipientDid: record.recipientDid,
    //   senderDid: record.actorDid,
    //   encryptedPayload: record.encryptedPayload,
    //   createdAt: record.createdAt,
    // });
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
