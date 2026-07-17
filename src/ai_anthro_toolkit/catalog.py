"""Registry of the toolkit's Colab notebooks.

Lets the MCP server point researchers at capabilities that exist as
notebooks — especially data collection — beyond the natively implemented
tools. Kept in sync with the repository README's notebook table.
"""

_COLAB = ("https://colab.research.google.com/github/"
          "MattArtzAnthro/AI-Anthropology-Toolkit/blob/main/notebooks/")
_GITHUB = ("https://github.com/MattArtzAnthro/AI-Anthropology-Toolkit/"
           "blob/main/notebooks/")


def _nb(name, file, category, description, run="colab"):
    return {
        "name": name,
        "category": category,
        "description": description,
        "run": run,
        "colab_url": _COLAB + file if run == "colab" else None,
        "github_url": _GITHUB + file,
    }


NOTEBOOKS = [
    # -- data collection ---------------------------------------------------
    _nb("Academic Literature Explorer", "Academic_Literature_Explorer.ipynb",
        "data_collection",
        "Search 250M+ scholarly works across all disciplines via OpenAlex with citation counts and open access detection"),
    _nb("Google Books Ngram Explorer", "Google_Books_Ngram_Explorer.ipynb",
        "data_collection",
        "Analyze historical word frequency patterns across Google Books corpora (1800-2022) with visualization and export"),
    _nb("Google Trends Explorer", "Google_Trends_Explorer.ipynb",
        "data_collection",
        "Retrieve and visualize Google Trends data with multi-term comparison, regional breakdowns, and related queries"),
    _nb("Google News Explorer", "Google_News_Explorer.ipynb",
        "data_collection",
        "Search Google News by keyword, time period, and country with quick or extended date-range modes"),
    _nb("Google Scholar Explorer", "Google_Scholar_Explorer.ipynb",
        "data_collection",
        "Search Google Scholar for publications with year filtering, citation counts, and structured export",
        run="local"),
    _nb("Google Patents Explorer", "Google_Patents_Explorer.ipynb",
        "data_collection",
        "Search Google Patents for patent metadata including titles, inventors, assignees, and filing dates"),
    _nb("YouTube Video Search", "YouTube_Video_Search.ipynb",
        "data_collection",
        "Search YouTube and export video metadata including titles, channels, views, and durations"),
    _nb("YouTube Transcript Fetcher", "YouTube_Transcript_Fetcher.ipynb",
        "data_collection",
        "Fetch YouTube video transcripts with language selection, segment chunking, and multiple export formats"),
    _nb("Podcast RSS Explorer", "Podcast_RSS_Explorer.ipynb",
        "data_collection",
        "Pull episode metadata from any podcast RSS feed with titles, dates, durations, and structured export"),
    _nb("PubMed Literature Harvester", "PubMed_Literature_Harvester.ipynb",
        "data_collection",
        "Search PubMed and enrich results with metadata from CrossRef, OpenAlex, and Semantic Scholar"),
    # -- qualitative analysis ----------------------------------------------
    _nb("Interview Transcript Semantic Chunker",
        "Interview_Transcript_Semantic_Chunker.ipynb", "analysis",
        "Segment interview transcripts into semantically coherent chunks with speaker-aware processing and coherence scoring — fully local, no API key required"),
    _nb("Qualitative Codebook Builder", "Qualitative_Codebook_Builder.ipynb",
        "analysis",
        "Build qualitative codebooks from source literature with AI-assisted code generation, validation, and structured export"),
    _nb("Coding and Thematic Analysis", "Coding_and_Thematic_Analysis.ipynb",
        "analysis",
        "Apply codes to qualitative data and build themes using deductive, inductive, or hybrid approaches, with multi-lens parallel analysis and cross-lens comparison"),
    # -- computational text analysis ---------------------------------------
    _nb("Text Network Analysis", "Text_Network_Analysis.ipynb", "text_analysis",
        "Build co-occurrence networks from text with community detection, centrality metrics, and interactive visualization"),
    _nb("Topic Modeling (BERTopic)", "Topic_Modeling_BERTopic.ipynb",
        "text_analysis",
        "Discover topics in text collections using transformer-based clustering with interactive visualizations and zero-shot mode"),
    _nb("Named Entity Recognition (GLiNER2)",
        "Named_Entity_Recognition_GLiNER2.ipynb", "text_analysis",
        "Extract people, places, organizations, concepts, and custom entity types from text using zero-shot NER"),
]


def list_notebooks(category: str = "") -> list[dict]:
    """Return the notebook catalog, optionally filtered by category."""
    if category:
        return [n for n in NOTEBOOKS if n["category"] == category]
    return list(NOTEBOOKS)
