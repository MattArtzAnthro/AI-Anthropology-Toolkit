"""Canonical analytical lens registry (42 lenses).

Extracted from the Qualitative Codebook Builder notebook, which remains the
authoritative definition; the drift test asserts parity between this module
and the notebook source.
"""

STANCE_DEFINITIONS = {
    "affect_theory": {
        "name": "Affect Theory",
        "description": "Pre-cognitive intensities, bodily capacities, and affective atmospheres.",
        "prompt_modifier": """Adopt an AFFECT THEORY analytical lens. Focus on:
- Pre-cognitive intensities, bodily capacities, and affective atmospheres
- How affect circulates between bodies, objects, and environments
- The distinction between affect (pre-personal intensity) and emotion (named feeling)
- Affective labor, contagion, and the politics of feeling
- Codes should capture felt intensities and atmospheric qualities beyond named emotions."""
    },
    "anarchist": {
        "name": "Anarchist / Anti-authoritarian",
        "description": "Mutual aid, horizontal organizing, and resistance to hierarchical authority.",
        "prompt_modifier": """Adopt an ANARCHIST / ANTI-AUTHORITARIAN analytical lens. Focus on:
- Mutual aid, solidarity, and horizontal forms of organizing
- Resistance to hierarchical authority, state power, and institutional coercion
- Prefigurative politics and autonomous community practices
- Direct action, self-governance, and voluntary association
- Codes should illuminate anti-hierarchical practices and grassroots self-organization."""
    },
    "business_organizational": {
        "name": "Business / Organizational",
        "description": "Organizational culture, corporate practices, and workplace dynamics.",
        "prompt_modifier": """Adopt a BUSINESS / ORGANIZATIONAL analytical lens. Focus on:
- Organizational culture, workplace norms, and institutional practices
- Management strategies, corporate decision-making, and innovation processes
- How cultural context shapes business practices and economic behavior
- Stakeholder dynamics, corporate social responsibility, and market logics
- Codes should capture organizational processes and workplace cultural dynamics."""
    },
    "cognitive": {
        "name": "Cognitive",
        "description": "Mental models, categorization, decision-making, and cultural cognition.",
        "prompt_modifier": """Adopt a COGNITIVE analytical lens. Focus on:
- Mental models, schemas, and categorization processes
- How cultural knowledge is organized, stored, and retrieved
- Decision-making heuristics, reasoning patterns, and folk theories
- Distributed cognition and the relationship between culture and thought
- Codes should capture cognitive processes, mental models, and reasoning patterns."""
    },
    "computational_digital": {
        "name": "Computational / Digital",
        "description": "Digital platforms, algorithmic systems, and data-mediated social life.",
        "prompt_modifier": """Adopt a COMPUTATIONAL / DIGITAL analytical lens. Focus on:
- Digital platforms, algorithmic mediation, and data-driven systems
- How technology shapes social interaction, identity, and community
- Digital labor, platform economies, and datafication of everyday life
- Methodological innovation in studying online and hybrid social worlds
- Codes should capture digital mediation, platform dynamics, and human-technology entanglements."""
    },
    "critical": {
        "name": "Critical",
        "description": "Power relations, structural constraints, and ideological formations.",
        "prompt_modifier": """Adopt a CRITICAL analytical lens. Focus on:
- Power dynamics, structural inequalities, and systemic constraints
- Ideological assumptions and hegemonic narratives
- Resistance, agency within constraint, and counter-narratives
- How macro-level forces shape individual experience
- Codes should illuminate domination, marginalization, and structural forces."""
    },
    "critical_medical": {
        "name": "Critical Medical",
        "description": "Biomedical power, medicalization, and the social production of health/illness.",
        "prompt_modifier": """Adopt a CRITICAL MEDICAL analytical lens. Focus on:
- Biomedical power, medicalization, and the social construction of disease categories
- How structural inequalities produce differential health outcomes
- Patient experience within institutional medical systems
- Pharmaceutical politics, clinical authority, and epistemic hierarchies in healthcare
- Codes should illuminate how medical systems produce and reproduce social inequalities."""
    },
    "critical_race": {
        "name": "Critical Race",
        "description": "Racial formations, systemic racism, and intersectional oppression.",
        "prompt_modifier": """Adopt a CRITICAL RACE analytical lens. Focus on:
- Racial formations, systemic racism, and the social construction of race
- Intersections of race with class, gender, sexuality, and other axes of power
- Counter-narratives, racial consciousness, and resistance to white supremacy
- Institutional racism, colorblind ideology, and racial microaggressions
- Codes should center racial dynamics and illuminate how racism operates structurally and interpersonally."""
    },
    "decolonial": {
        "name": "Decolonial",
        "description": "Colonial matrices of power, epistemic violence, and pluriversal alternatives.",
        "prompt_modifier": """Adopt a DECOLONIAL analytical lens. Focus on:
- Colonial matrices of power and the persistence of coloniality in knowledge production
- Epistemic violence, subaltern knowledge, and border thinking
- Pluriversal alternatives to Western-centric universalism
- Land, sovereignty, and the politics of who produces legitimate knowledge
- Codes should foreground resistance to colonial epistemologies and center marginalized knowledge systems."""
    },
    "design_anthropology": {
        "name": "Design Anthropology",
        "description": "Design processes, co-creation, future-making, and material interventions.",
        "prompt_modifier": """Adopt a DESIGN ANTHROPOLOGY analytical lens. Focus on:
- Design processes as cultural practices of future-making and world-shaping
- Co-creation, participatory design, and collaborative prototyping
- How designed objects and systems mediate social relations
- The politics of design decisions and their material consequences
- Codes should capture design practices, material interventions, and speculative futures."""
    },
    "economic_anthropology": {
        "name": "Economic Anthropology",
        "description": "Exchange systems, value creation, labor, and economic pluralism.",
        "prompt_modifier": """Adopt an ECONOMIC ANTHROPOLOGY analytical lens. Focus on:
- Diverse economies, exchange systems, and forms of value creation
- Labor, livelihoods, and the social embeddedness of economic activity
- Gift economies, reciprocity, redistribution, and market logics
- How economic practices are culturally constituted and morally evaluated
- Codes should capture economic practices, value systems, and material livelihood strategies."""
    },
    "environmental_political_ecology": {
        "name": "Environmental / Political Ecology",
        "description": "Human-environment relations, resource politics, and ecological knowledge.",
        "prompt_modifier": """Adopt an ENVIRONMENTAL / POLITICAL ECOLOGY analytical lens. Focus on:
- Human-environment relations and the politics of natural resource access and control
- Environmental knowledge, ecological practices, and landscape management
- Climate change, environmental justice, and uneven ecological vulnerabilities
- How power shapes who benefits from and bears the costs of environmental change
- Codes should capture environmental practices, resource politics, and ecological knowledge systems."""
    },
    "evaluation": {
        "name": "Evaluation",
        "description": "Program effectiveness, practical outcomes, and stakeholder perspectives.",
        "prompt_modifier": """Adopt an EVALUATION analytical lens. Focus on:
- Program effectiveness, implementation fidelity, and practical outcomes
- Stakeholder perspectives, needs assessments, and utilization-focused analysis
- What works, for whom, under what conditions, and why
- Actionable findings, recommendations, and evidence for decision-making
- Codes should capture program processes, outcomes, and stakeholder experiences relevant to improvement."""
    },
    "feminist": {
        "name": "Feminist",
        "description": "Gendered power, patriarchy, intersectionality, and embodied experience.",
        "prompt_modifier": """Adopt a FEMINIST analytical lens. Focus on:
- Gendered power relations, patriarchal structures, and intersecting oppressions
- Embodied experience, reproductive labor, and the politics of care
- How gender norms are produced, performed, and contested
- Feminist epistemology: situated knowledge, standpoint, and reflexivity
- Codes should illuminate gendered dynamics, intersectional power, and women's/marginalized experiences."""
    },
    "hermeneutic": {
        "name": "Hermeneutic",
        "description": "Interpretation, the hermeneutic circle, textual meaning, and understanding.",
        "prompt_modifier": """Adopt a HERMENEUTIC analytical lens. Focus on:
- Processes of interpretation and the hermeneutic circle (part-whole relationships)
- How meaning is constituted through dialogue between text, context, and interpreter
- Pre-understanding, prejudice (in the Gadamerian sense), and horizons of meaning
- The conditions under which understanding becomes possible
- Codes should capture interpretive processes, meaning-making, and the contextual conditions of understanding."""
    },
    "historical_archival": {
        "name": "Historical / Archival",
        "description": "Historical processes, archival sources, memory, and temporal change.",
        "prompt_modifier": """Adopt a HISTORICAL / ARCHIVAL analytical lens. Focus on:
- Historical processes, temporal change, and the longue durée of social phenomena
- Archival sources, documentary evidence, and the politics of the archive
- Collective memory, oral history, and contested narratives of the past
- How present conditions are shaped by historical trajectories and path dependencies
- Codes should capture historical processes, temporal dynamics, and the relationship between past and present."""
    },
    "indigenous_methodologies": {
        "name": "Indigenous Methodologies",
        "description": "Relational accountability, community sovereignty, and Indigenous knowledge systems.",
        "prompt_modifier": """Adopt an INDIGENOUS METHODOLOGIES analytical lens. Focus on:
- Relational accountability, reciprocity, and community-centered research ethics
- Indigenous knowledge systems, oral traditions, and land-based epistemologies
- Sovereignty over knowledge production and community self-determination
- Storytelling as method, ceremony as research practice, and place-based knowing
- Codes should center Indigenous ways of knowing, relational ethics, and community sovereignty over knowledge."""
    },
    "infrastructure_studies": {
        "name": "Infrastructure Studies",
        "description": "Built systems, maintenance, breakdown, and the politics of infrastructure.",
        "prompt_modifier": """Adopt an INFRASTRUCTURE STUDIES analytical lens. Focus on:
- Built systems, technical networks, and their social embedding
- Maintenance, repair, breakdown, and the labor of keeping systems running
- How infrastructure becomes visible only upon failure
- The politics of infrastructure: who is served, who is excluded, and who maintains
- Codes should capture infrastructural arrangements, maintenance practices, and the social life of technical systems."""
    },
    "interpretive": {
        "name": "Interpretive",
        "description": "Meaning-making processes, lived experience, and participant perspectives.",
        "prompt_modifier": """Adopt an INTERPRETIVE analytical lens. Focus on:
- Meaning-making processes and subjective experiences
- How participants interpret and construct their social worlds
- Lived experience, emotions, and sense-making narratives
- Cultural symbols, language use, and interpretive frameworks
- Codes should capture how subjects understand their own experiences."""
    },
    "legal_rights_based": {
        "name": "Legal / Rights-based",
        "description": "Legal frameworks, rights claims, justice, and normative orders.",
        "prompt_modifier": """Adopt a LEGAL / RIGHTS-BASED analytical lens. Focus on:
- Legal frameworks, rights claims, and normative orders
- How law is produced, interpreted, and experienced in everyday life
- Legal pluralism, customary law, and the gaps between law-on-paper and law-in-practice
- Justice, access to legal remedies, and the politics of rights discourse
- Codes should capture legal processes, rights claims, and the lived experience of legal systems."""
    },
    "linguistic": {
        "name": "Linguistic",
        "description": "Language structure, discourse patterns, and communicative practices.",
        "prompt_modifier": """Adopt a LINGUISTIC analytical lens. Focus on:
- Language structure, discourse patterns, and communicative practices
- How language constitutes social reality, identity, and relationships
- Code-switching, register, indexicality, and language ideologies
- The pragmatics of speech: what utterances do in social context
- Codes should capture linguistic patterns, discourse strategies, and the social work of language."""
    },
    "material_culture": {
        "name": "Material Culture / Object-oriented",
        "description": "Objects, things, material agency, and human-object entanglements.",
        "prompt_modifier": """Adopt a MATERIAL CULTURE / OBJECT-ORIENTED analytical lens. Focus on:
- Objects, artifacts, and their social lives and trajectories
- Material agency: how things shape, enable, and constrain human action
- Human-object entanglements, assemblages, and material semiosis
- Craft, making, consumption, and the cultural biography of things
- Codes should capture object-human relationships, material practices, and the agency of things."""
    },
    "medical_health_interpretive": {
        "name": "Medical / Health (interpretive)",
        "description": "Illness experience, healing practices, and health-seeking behavior.",
        "prompt_modifier": """Adopt a MEDICAL / HEALTH (INTERPRETIVE) analytical lens. Focus on:
- Illness experience, suffering narratives, and explanatory models of sickness
- Healing practices, therapeutic pluralism, and health-seeking behavior
- The body as a site of cultural inscription and lived experience
- How individuals and communities make sense of health, illness, and care
- Codes should capture illness experiences, healing narratives, and culturally situated health practices."""
    },
    "migration_mobility": {
        "name": "Migration / Mobility Studies",
        "description": "Movement, displacement, borders, and transnational connections.",
        "prompt_modifier": """Adopt a MIGRATION / MOBILITY STUDIES analytical lens. Focus on:
- Movement, displacement, and the politics of borders and belonging
- Transnational connections, diasporic identities, and mobile livelihoods
- Immigration regimes, documentation status, and bureaucratic encounters
- How mobility and immobility are structured by race, class, gender, and geopolitics
- Codes should capture mobility practices, border experiences, and transnational social fields."""
    },
    "mixed_methods": {
        "name": "Mixed-methods",
        "description": "Integration of qualitative and quantitative approaches for complementary insight.",
        "prompt_modifier": """Adopt a MIXED-METHODS analytical lens. Focus on:
- Phenomena amenable to both qualitative interpretation and quantitative measurement
- Patterns that can be triangulated across data types and methods
- Convergence and divergence between qualitative and quantitative findings
- Practical outcomes, transferability, and generalizable insights
- Codes should be concrete enough for quantification while preserving qualitative richness."""
    },
    "multi_sited": {
        "name": "Multi-sited",
        "description": "Connections across sites, following flows of people, things, and ideas.",
        "prompt_modifier": """Adopt a MULTI-SITED analytical lens. Focus on:
- Connections, flows, and circulations across multiple geographic or social sites
- How phenomena manifest differently across locations while remaining connected
- Following people, things, metaphors, or conflicts across institutional and spatial boundaries
- The construction of the field through tracing relations rather than bounding a single site
- Codes should capture cross-site connections, circulations, and the multi-scalar nature of phenomena."""
    },
    "multispecies": {
        "name": "Multispecies / More-than-human",
        "description": "Interspecies relations, non-human agencies, and ecological entanglements.",
        "prompt_modifier": """Adopt a MULTISPECIES / MORE-THAN-HUMAN analytical lens. Focus on:
- Interspecies relations, symbiosis, and multispecies entanglements
- Non-human agencies, animal perspectives, and more-than-human sociality
- How human worlds are co-constituted with plants, animals, fungi, and microbes
- Ecological intimacies, companion species, and the breakdown of nature/culture divides
- Codes should capture interspecies relationships and extend analytical attention beyond the exclusively human."""
    },
    "narrative_life_history": {
        "name": "Narrative / Life History",
        "description": "Storytelling, biographical narratives, and the temporal structuring of experience.",
        "prompt_modifier": """Adopt a NARRATIVE / LIFE HISTORY analytical lens. Focus on:
- Storytelling practices, narrative structure, and biographical trajectories
- How people construct coherent life stories from fragmented experiences
- Plot, temporality, emplotment, and turning points in personal narratives
- The social and cultural shaping of what stories can be told and how
- Codes should capture narrative structures, life story elements, and the temporal organization of experience."""
    },
    "ontological": {
        "name": "Ontological",
        "description": "Multiple worlds, radical difference, and what exists beyond epistemology.",
        "prompt_modifier": """Adopt an ONTOLOGICAL analytical lens. Focus on:
- Ontological difference: multiple worlds rather than multiple perspectives on one world
- What exists, what kinds of beings populate the world, and how reality is constituted
- Taking seriously non-Western ontologies without reducing them to cultural belief
- The politics of ontology: whose reality counts and how worlds are made and unmade
- Codes should attend to ontological commitments, world-making practices, and radical difference in what is real."""
    },
    "performance_performativity": {
        "name": "Performance / Performativity",
        "description": "Social performances, ritual enactments, and performative constitution of identity.",
        "prompt_modifier": """Adopt a PERFORMANCE / PERFORMATIVITY analytical lens. Focus on:
- Social performances, staged interactions, and ritual enactments
- How identities, genders, and social categories are performatively constituted
- The distinction between theatrical performance and performativity (Butler, Austin)
- Embodied practice, gesture, spectacle, and the aesthetics of everyday interaction
- Codes should capture performative acts, ritual practices, and how social realities are enacted into being."""
    },
    "phenomenological": {
        "name": "Phenomenological",
        "description": "First-person lived experience, structures of consciousness, and embodiment.",
        "prompt_modifier": """Adopt a PHENOMENOLOGICAL analytical lens. Focus on:
- First-person lived experience and the structures of consciousness
- Pre-reflective and embodied dimensions of experience
- Epoché: bracketing assumptions to attend to phenomena as they appear
- Temporality, spatiality, and intersubjective dimensions of experience
- Codes should capture the essential structures of how phenomena are experienced."""
    },
    "political_economy_marxian": {
        "name": "Political Economy / Marxian",
        "description": "Class relations, labor, capital accumulation, and structural exploitation.",
        "prompt_modifier": """Adopt a POLITICAL ECONOMY / MARXIAN analytical lens. Focus on:
- Class relations, labor exploitation, and capital accumulation processes
- How economic structures shape social relations, consciousness, and everyday life
- Commodification, alienation, and the production of surplus value
- The relationship between base and superstructure, ideology, and material conditions
- Codes should illuminate class dynamics, labor processes, and structural economic forces."""
    },
    "postcolonial": {
        "name": "Postcolonial",
        "description": "Colonial legacies, subaltern voices, hybridity, and imperial power.",
        "prompt_modifier": """Adopt a POSTCOLONIAL analytical lens. Focus on:
- Colonial legacies and their ongoing effects on formerly colonized societies
- Subaltern voices, representation, and the question of who speaks for whom
- Hybridity, mimicry, and the ambivalence of colonial encounters
- Imperial knowledge systems and their persistent influence on contemporary institutions
- Codes should illuminate colonial residues, subaltern perspectives, and the enduring asymmetries of imperial power."""
    },
    "practice_theory": {
        "name": "Practice Theory",
        "description": "Habitus, embodied routines, and the reproduction of social structures through practice.",
        "prompt_modifier": """Adopt a PRACTICE THEORY analytical lens. Focus on:
- Embodied routines, habitual dispositions, and practical know-how
- How social structures are reproduced and transformed through everyday practices
- Habitus, fields, and the interplay of structure and agency (Bourdieu)
- Material arrangements, bodily competences, and shared understandings that compose practices
- Codes should capture recurring practices, embodied routines, and how social order is produced through doing."""
    },
    "psychoanalytic": {
        "name": "Psychoanalytic",
        "description": "Unconscious processes, desire, fantasy, and psychic dimensions of culture.",
        "prompt_modifier": """Adopt a PSYCHOANALYTIC analytical lens. Focus on:
- Unconscious processes, repression, and the psychic life of social structures
- Desire, fantasy, identification, and their role in cultural reproduction
- Transference, projection, and affective dynamics in social relationships
- How collective anxieties, traumas, and defenses shape cultural formations
- Codes should capture unconscious dynamics, psychic investments, and the emotional undercurrents of social life."""
    },
    "psychological": {
        "name": "Psychological",
        "description": "Individual experience, mental processes, motivation, and well-being.",
        "prompt_modifier": """Adopt a PSYCHOLOGICAL analytical lens. Focus on:
- Individual experience, mental processes, and psychological well-being
- Motivation, coping strategies, and adaptive behavior
- Self-concept, identity formation, and developmental trajectories
- Cognitive and emotional responses to social and environmental conditions
- Codes should capture individual psychological processes, subjective states, and person-level experiences."""
    },
    "public_engaged": {
        "name": "Public / Engaged",
        "description": "Public impact, community engagement, and research as social intervention.",
        "prompt_modifier": """Adopt a PUBLIC / ENGAGED analytical lens. Focus on:
- Public impact, civic engagement, and the social responsibility of research
- Community partnerships, participatory processes, and collaborative knowledge production
- How research can serve communities and contribute to social change
- Translation of findings for public audiences and policy-relevant insights
- Codes should capture publicly relevant dynamics, community needs, and opportunities for engaged scholarship."""
    },
    "queer_theory": {
        "name": "Queer Theory",
        "description": "Heteronormativity, sexuality, gender fluidity, and the politics of deviance.",
        "prompt_modifier": """Adopt a QUEER THEORY analytical lens. Focus on:
- Heteronormativity, compulsory heterosexuality, and the regulation of desire
- Gender fluidity, non-binary identities, and the instability of sexual categories
- How deviance, transgression, and non-normativity challenge social order
- Queer temporalities, kinship formations, and anti-normative world-making
- Codes should illuminate heteronormative assumptions, gender/sexual fluidity, and queer modes of being."""
    },
    "semiotic": {
        "name": "Semiotic",
        "description": "Sign systems, meaning, codes, and the cultural production of significance.",
        "prompt_modifier": """Adopt a SEMIOTIC analytical lens. Focus on:
- Sign systems, codes, and the cultural production of meaning
- How signs (icons, indexes, symbols) mediate social reality
- Intertextuality, connotation, and the layering of cultural meanings
- Semiotic ideologies: beliefs about how signs work and what they represent
- Codes should capture semiotic processes, sign relationships, and the cultural machinery of meaning-making."""
    },
    "structuralist_post_structuralist": {
        "name": "Structuralist / Post-structuralist",
        "description": "Deep structures, binary oppositions, discourse, and the instability of meaning.",
        "prompt_modifier": """Adopt a STRUCTURALIST / POST-STRUCTURALIST analytical lens. Focus on:
- Deep structures, binary oppositions, and underlying systems of classification
- Discourse, power/knowledge, and how language constitutes social reality (Foucault)
- The instability, deferral, and deconstruction of meaning (Derrida)
- How subjects are constituted through discursive practices and disciplinary regimes
- Codes should capture structural patterns, discursive formations, and the constitutive role of language and classification."""
    },
    "sts_actor_network": {
        "name": "STS / Actor-Network",
        "description": "Heterogeneous networks of human and non-human actants; co-production of knowledge and society.",
        "prompt_modifier": """Adopt an STS / ACTOR-NETWORK THEORY analytical lens. Focus on:
- Heterogeneous networks of human and non-human actants
- Translation, enrollment, and stabilization of actor-networks
- How facts, technologies, and social order are co-produced
- Controversies, black-boxing, and obligatory passage points
- Codes should trace associations between actants without privileging human agency."""
    },
    "visual_sensory": {
        "name": "Visual / Sensory",
        "description": "Visual culture, sensory experience, and non-textual modes of knowing.",
        "prompt_modifier": """Adopt a VISUAL / SENSORY analytical lens. Focus on:
- Visual culture, image-making, and the politics of representation
- Sensory experience: sight, sound, smell, taste, touch as modes of knowing
- How non-textual media (photographs, film, objects, soundscapes) convey meaning
- Embodied perception, synaesthesia, and culturally shaped sensoriums
- Codes should capture visual and sensory dimensions of experience, including non-verbal and non-textual phenomena."""
    },
}

LENSES = STANCE_DEFINITIONS  # public alias


def get_lens(key: str) -> dict:
    """Return one lens definition by registry key (e.g. 'critical_race')."""
    return STANCE_DEFINITIONS[key]


def find_lens(name_or_key: str) -> tuple[str, dict] | None:
    """Resolve a lens by key or display name, case-insensitively."""
    q = name_or_key.strip().lower()
    for key, entry in STANCE_DEFINITIONS.items():
        if q in (key.lower(), entry["name"].lower()):
            return key, entry
    return None
