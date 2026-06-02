/**
 * Mirrors the com.etzhayyim.apps.openIsco.occupation Lexicon record shape.
 * Source: 00-contracts/lexicons/com/etzhayyim/apps/openIsco/occupation.json
 */
export interface Occupation {
  /** ISCO-08 numeric code, 4 digits. e.g. "2511". */
  code: string;

  /** Human-readable occupation name (English). */
  name: string;

  /** ISCO-08 major group code, 1 digit. Parent of `subMajor`. */
  major: string;

  /** Sub-major group code, 2 digits. Parent of `minor`. */
  subMajor?: string;

  /** Minor group code, 3 digits. Parent of `unitGroup`. */
  minor?: string;

  /** Unit group code, 4 digits (= `code`). */
  unitGroup?: string;

  /** ISCO description text. */
  description?: string;

  /**
   * Optional CID of the published ISCO handbook chapter PDF.
   * Set by the seeder after `e.write({ blobs: { handbook: pdfBlob } })`.
   */
  handbookCid?: string;

  /** ISO date when this occupation entry was published in the ISCO revision. */
  publishedAt: string;
}
