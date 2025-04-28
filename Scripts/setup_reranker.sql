select azure_ai.set_setting('azure_ml.scoring_endpoint','');
select azure_ai.set_setting('azure_ml.endpoint_key', '');

CREATE OR REPLACE FUNCTION semantic_relevance(query TEXT, n INT)
RETURNS jsonb AS $$
DECLARE
    json_pairs jsonb;
	result_json jsonb;
BEGIN
	json_pairs := generate_json_pairs(query, n);
	result_json := azure_ml.invoke(
				json_pairs,
				deployment_name=>'bge-v2-m3-1',
				timeout_ms => 180000);
	RETURN (
		SELECT result_json as result
	);
END $$ LANGUAGE plpgsql;

CREATE OR REPLACE FUNCTION generate_json_pairs(query TEXT, n INT)
RETURNS jsonb AS $$
BEGIN
    RETURN (
        SELECT jsonb_build_object(
            'pairs', 
            jsonb_agg(
                jsonb_build_array(query, LEFT(text, 800))
            )
        ) AS result_json
        FROM (
            SELECT id, opinion AS text
		    FROM cases
		    ORDER BY opinions_vector <=> azure_openai.create_embeddings('text-embedding-3-small', query)::vector
		    LIMIT n
        ) subquery
    );
END $$ LANGUAGE plpgsql;