/*
A bunch of queries that I've used frequently
*/
SELECT COUNT(*) FROM paper_assessments WHERE is_neurosymbolic = 1;
SELECT * FROM papers WHERE doi = '10.1007/s00521-024-09960-z';
SELECT * FROM paper_assessments WHERE paper_id = 433;
SELECT COUNT(*) FROM papers WHERE processed != 1;

SELECT COUNT(*)
FROM papers p
         JOIN paper_assessments a ON p.id = a.paper_id
WHERE p.processed = 1;


SELECT id, title, file_path
FROM papers
WHERE file_path IS NOT NULL
  AND id = 7

SELECT *
FROM papers p
         JOIN paper_assessments a
              ON p.id = a.paper_id
WHERE publication_source = 'acm.bib'
AND summary IS NOT NULL;

SELECT *
FROM papers p
JOIN paper_assessments a
ON p.id = a.paper_id
JOIN rel_keywords_papers k
ON p.id = k.paper_id
WHERE a.is_neurosymbolic = 1
AND a.is_development = 1
