# Identity Leaks a Placeholder Cannot Fix

Reference file for the review-anonymization skill. Loaded at the sweep for
everything that identifies the authors after their names are gone.

The governing test is the **insider test**: not "is the name removed?" but
"could a reviewer in this subfield name the author from what remains?"
Anthropology fails it in its own ways. A distinctive fieldsite plus a
citation trail identifies an ethnographer as surely as a byline.

Every finding here goes to the author with options. None is reworded by
the skill.

---

## 1. The Hard Rule: Participants First

Author anonymization never weakens a participant protection. Check these
before any substitution runs:

- **Never replace a participant pseudonym with a real name,** and never
  let a find string reach one. An author's surname can also be a
  pseudonym in the manuscript.
- **Never re-identify a fieldsite the manuscript disguised.** Masking a
  self-citation is what keeps a reviewer from linking the disguised site
  to an earlier publication that named it; the fix is the mask, never the
  name.
- **Never move identifying participant detail to the title page** or the
  note to the editor. The title page is about the authors.
- **Never alter quoted speech, kin terms, or orthography** to hide the
  author. They are evidence.

Where hiding the author and protecting a participant conflict, stop and
route it: the informed-consent skill for what participants agreed to, the
irb-protocol skill for the de-identification plan.

## 2. Leaks in Any Manuscript

| Leak | Example (invented) | Why a placeholder fails |
|---|---|---|
| Role descriptors | "the original creator of the tool and an author of this article" | The role names the person without the name |
| Repository URLs and handles | `github.com/dreyes/...`, an OSF project under a personal account | The name is inside the address |
| Link targets | Display text "the project repository" over a URL with a username | The URL is in the file, not on the page |
| A sentence tying an author to a cited work | "his own paper with Okafor and Lindqvist (Okafor et al. 2021)" | The reference list names him even if the sentence does not |
| Quoted public posts by an author | A blog post or social media post quoted as data | One search finds the account |
| First-person research history | "in my dissertation," "our lab," "my earlier study" | Biography without a name |
| Coined terms | "what I have elsewhere called ..." | The term is a byline |
| Preprints and dissertations | The same title in a repository | One search finds it; a policy question, not a fix |

Options for each: the author rewords it, it is masked with a bracketed
note, or it stays and is mentioned to the editor. For links, an anonymized
view-only link where the host supports one (OSF view-only links can hide
contributor names) or `[repository link removed for peer review]`.

## 3. Leaks Particular to Ethnography

Sweep for each, and report what it reveals in combination, since most of
these identify only in pairs:

- **The fieldsite plus first-person fieldwork.** "My fieldwork in" or "my
  years with" beside a named or recognizable site.
- **Years in the field.** "Eighteen months between 2019 and 2021" matched
  against a funder's award list or a dissertation date.
- **Prior monographs or articles on the same community.** The citation
  trail is the strongest leak there is; a single-authored book on the same
  village, cited three times, names its author.
- **Named interlocutors, collaborators, and hosts** known to work with one
  ethnographer: a key interlocutor who appears in the author's earlier
  work, a host institution, a permit sponsor, a local co-researcher.
- **Positionality and reflexive passages.** Nationality, gender, religion,
  kin position, and training together form a profile. The categories doing
  analytical work ("a researcher who shares the community's language but
  not its religion") usually survive; the biography around them usually
  does not.
- **Acknowledgements** of communities, research assistants, transcribers,
  and translators. Move them to the title page whole.
- **Ethics protocol numbers, research permit numbers, and grant numbers.**
  Each is searchable, and some national permit registers list the
  researcher by name. Move them to the title page, or use a bracketed
  placeholder where the venue wants the statement kept in the main
  document.
- **Photographs** that show the author, the author's household or field
  family, or a caption crediting the author by name. "Photograph by the
  author" is fine; a named credit is not.
- **Language and kin terms that place the ethnographer.** A kinship name
  the community gave the author, a term of address used for them, or a
  dialect form recorded only in their earlier work.
- **Data deposits.** An archive deposit (a language archive, a qualitative
  data repository) with the depositor named.

Some of these cannot be removed without damaging the ethnography. That is
the author's trade, and the decision list records it.

## 4. Do Not Over-Anonymize

- **Standard co-authored works stay.** A well-known multi-author paper an
  author contributed to remains an ordinary citation when nothing in the
  text ties it to an author. Masking it draws attention and removes a
  citation reviewers expect.
- **Do not delete self-citations.** Masked citations keep their place and
  year, so reviewers can see that prior work exists.
- **Some papers cannot be fully anonymized.** A paper about a named tool,
  a well-known project, or a fieldsite only one person works in will be
  recognized by some reviewers. Say so plainly. Review policies accept
  this, and the note to the editor is the place to say it.
- **Not everything in the file is identity.** Document language and
  proofing tags, editing-session identifiers, and style names reveal
  nothing about the author and are left alone.

## 5. The Insider Test

After the substitutions and the author's decisions, read the copy as the
two or three people most likely to review it: the area specialist, the
subfield theorist, the methodological neighbour. What combination of site,
years, method, framework, and citation pattern still points at the author?
Anything that survives goes on the decision list or into the note to the
editor, and the author decides which.
