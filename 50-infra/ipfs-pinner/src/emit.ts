export interface PinEmitOpts {
  did: string;
  carPath: string;
  cid: string;
  providers: string[];
  pinnedAt: string;
}

export async function emitPinRecord(_opts: PinEmitOpts): Promise<void> {
  throw new Error(
    "[ipfs-pinner/emit] TODO: createRecord under ai.gftd.apps.substrate.ipfsPin " +
      "with {cid, providers, pinnedAt, carCid (= cid)}."
  );
}
