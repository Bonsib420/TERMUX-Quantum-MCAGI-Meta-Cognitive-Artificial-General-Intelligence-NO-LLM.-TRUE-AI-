        concept_scores = engine.extract_concepts_scored(user_input) if hybrid_gen else []

        r_hybrid = hybrid_gen.generate(
            user_input,
            concepts,
            concept_scores,
            min_words=10,
            max_words=25
        ) if hybrid_gen else ""

        r_casual = engine.generate_response(
            user_input,
            questions,
            understanding,
            concepts,
            growth_stage=growth_stage
        )

        response = r_hybrid if len(r_hybrid) > len(r_casual) else r_casual

        if questions:
            q = questions[0] if isinstance(questions[0], str) else questions[0].get("question", "")
            response = response + " " + q
