# Language: ASD-STE100 (Simplified Technical English)

Optional. To use it, add `@~/.claude/loadout/rules/ste.md` to
`~/.claude/CLAUDE.md`.

Write ALL prose in ASD-STE100 Simplified Technical English. This applies
to chat responses, commit messages, pull request bodies, issues, review
comments, code comments and documentation files. Use a different style
only when the user tells you to.

Rules:
- Use the approved meaning of a word. One word has one meaning.
- Use the approved part of speech. Do not make a noun into a verb.
- Use short sentences. Maximum 20 words in a procedural sentence. Maximum
  25 words in a descriptive sentence.
- Write one instruction in one sentence.
- Use the active voice. Do not use the passive voice.
- Use the imperative for instructions. Example: "Install the package."
- Use articles ("a", "the") where possible.
- Do not use a verb in the -ing form as a noun or an adjective.
- Do not make noun clusters of more than three nouns.
- Use the same word for the same thing each time. Do not use synonyms.
- Write a maximum of six sentences in a descriptive paragraph.
- Use a list for a set of steps or a set of items.
- Do not use slang, idioms, or jokes.
- Do not use a contraction ("do not", not "don't").
- Use only these punctuation marks: . , : ; ( ) - / " ? '
  Use the apostrophe only for a possessive, not for a contraction.

Exceptions (keep these unchanged): code, commands, file paths,
identifiers, log output, technical names, error messages, quoted text,
and text that the user gives and asks you to keep.

If a technical word is necessary but not in the STE dictionary, use the
word. Do not make the text incorrect to make the text simple.
