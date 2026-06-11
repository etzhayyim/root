import { json } from '@sveltejs/kit';
import type { RequestHandler } from './$types';

const APP_DID = 'did:web:yoro.etzhayyim.com';
const PDS_ENDPOINT = 'https://pds.etzhayyim.com';

export const GET: RequestHandler = ({ platform }) => {
  const pubKey = String((platform as any)?.env?.SIGNING_PUBLIC_KEY ?? '').trim();
  return json(
    {
      '@context': ['https://www.w3.org/ns/did/v1', 'https://w3id.org/security/multikey/v1'],
      id: APP_DID,
      verificationMethod: pubKey
        ? [{
            id: `${APP_DID}#atproto`,
            type: 'Multikey',
            controller: APP_DID,
            publicKeyMultibase: pubKey,
          }]
        : [],
      service: [{
        id: '#atproto_pds',
        type: 'AtprotoPersonalDataServer',
        serviceEndpoint: PDS_ENDPOINT,
      }],
    },
    { headers: { 'cache-control': 'public, max-age=300' } },
  );
};
