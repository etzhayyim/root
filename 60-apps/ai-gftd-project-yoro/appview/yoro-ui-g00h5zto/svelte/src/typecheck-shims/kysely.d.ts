// CHARTER-VIOLATION §substrate (centralized DB forbidden — migrate to AT MST + IPFS + Base L2)
declare module 'kysely' {
  export const sql: any;

  export class DummyDriver {}
  export class PostgresAdapter {}
  export class PostgresQueryCompiler {}

  export class Kysely<T = any> {
    constructor(config?: any);
    selectFrom(...args: any[]): any;
    getExecutor(): any;
  }
}
