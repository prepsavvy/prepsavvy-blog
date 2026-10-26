SELECT d.year,d.unitid,i.institution,i.state,i.city,i.control,i.sector,
      d.cipcode,d.awards,d.reporting_flag
      FROM (SELECT run_id, record_id, collected_at,
  CAST(JSON_VALUE(payload, '$.year') AS INT64) AS year,
  JSON_VALUE(payload, '$.UNITID') AS unitid,
  JSON_VALUE(payload, '$.CIPCODE') AS cipcode,
  CAST(JSON_VALUE(payload, '$.AWLEVEL') AS INT64) AS award_level,
  CAST(JSON_VALUE(payload, '$.CTOTALT') AS INT64) AS awards,
  JSON_VALUE(payload, '$.XCTOTALT') AS reporting_flag
FROM (SELECT r.* FROM `prepsavvy-prod.prepsavvy_research.records` r
              JOIN `prepsavvy-prod.prepsavvy_research.runs` m USING(source_id,run_id)
              WHERE m.status='complete' AND r.run_id IN UNNEST(@source_runs)
              AND NOT EXISTS(SELECT 1 FROM `prepsavvy-prod.prepsavvy_research.run_reviews` q
                WHERE q.run_id=r.run_id AND q.review_state='quarantined'))
WHERE source_id = 'ipeds' AND JSON_VALUE(payload, '$.kind') = 'degree') d
      JOIN (SELECT run_id, record_id, collected_at,
  CAST(JSON_VALUE(payload, '$.year') AS INT64) AS year,
  JSON_VALUE(payload, '$.UNITID') AS unitid,
  JSON_VALUE(payload, '$.INSTNM') AS institution,
  JSON_VALUE(payload, '$.CITY') AS city,
  JSON_VALUE(payload, '$.STABBR') AS state,
  JSON_VALUE(payload, '$.CONTROL') AS control,
  JSON_VALUE(payload, '$.SECTOR') AS sector,
  JSON_VALUE(payload, '$.COUNTYNM') AS county,
  JSON_VALUE(payload, '$.CBSA') AS cbsa,
  SAFE_CAST(JSON_VALUE(payload, '$.LATITUDE') AS FLOAT64) AS latitude,
  SAFE_CAST(JSON_VALUE(payload, '$.LONGITUD') AS FLOAT64) AS longitude,
  JSON_VALUE(payload, '$.WEBADDR') AS website
FROM (SELECT r.* FROM `prepsavvy-prod.prepsavvy_research.records` r
              JOIN `prepsavvy-prod.prepsavvy_research.runs` m USING(source_id,run_id)
              WHERE m.status='complete' AND r.run_id IN UNNEST(@source_runs)
              AND NOT EXISTS(SELECT 1 FROM `prepsavvy-prod.prepsavvy_research.run_reviews` q
                WHERE q.run_id=r.run_id AND q.review_state='quarantined'))
WHERE source_id = 'ipeds' AND JSON_VALUE(payload, '$.kind') = 'institution') i USING(year,unitid)
      WHERE d.award_level=5 AND d.year IN UNNEST(@years)
      AND i.state IN UNNEST(@states)
      AND (d.cipcode='99' OR REGEXP_CONTAINS(d.cipcode,r'^(16|23|38|54)\.[0-9]{4}$')
           OR d.cipcode='24.0103')
      ORDER BY d.year,d.unitid,d.cipcode