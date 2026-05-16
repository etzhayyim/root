CREATE FUNCTION cosine_similarity_real(a real[], b real[]) RETURNS real
    LANGUAGE sql IMMUTABLE AS $$
      SELECT CASE
        WHEN COALESCE(array_length(a, 1), 0) = 0 OR COALESCE(array_length(b, 1), 0) = 0 THEN 0::real
        ELSE (
          SELECT (
            SUM(av.v::double precision * bv.v::double precision)
            / NULLIF(
                sqrt(SUM(av.v::double precision * av.v::double precision))
                * sqrt(SUM(bv.v::double precision * bv.v::double precision)),
                0
              )
          )::real
          FROM unnest(a) WITH ORDINALITY AS av(v, i)
          JOIN unnest(b) WITH ORDINALITY AS bv(v, i) USING (i)
        )
      END
    $$;
