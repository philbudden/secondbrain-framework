---
name: pdf-to-markdown
description: Convert a supplied PDF into a faithful, human-readable Markdown copy, preserving reading order, notes, references, and meaningful visuals. Requires a fresh online URL from the user for each conversion. Use for PDF-to-Markdown transcription or source-format replacement, not for wiki ingestion or a summary.
---

# PDF to Markdown

Create a Markdown version of the supplied PDF that a person can read without opening the PDF. Preserve the author's content and sequence; do not paraphrase, correct substantive claims, or replace the article with an extraction dump.

Each invocation needs a fresh online URL for that PDF from the user. If the request omits it, ask for the URL while continuing any PDF inspection that does not depend on it. Do not reuse a URL from an earlier conversion or substitute a guessed DOI or local PDF link.

## Read the PDF

1. Inspect page count, metadata, text extraction, and images. Useful tools include `pdfinfo`, `pdftotext -layout`, and `pdfimages -list`.
2. Render every page at thumbnail size to check reading order, columns, tables, figures, and page-specific exceptions. Inspect relevant pages at readable size. A PDF can contain vector visuals even when `pdfimages` reports none.
3. For scans, use OCR if available and compare its output against rendered pages. Do not present uncertain OCR as verified text.

## Build the Markdown

- Keep the title, author and publication details, abstract, epigraphs, section hierarchy, prose, quotations, lists, tables, equations, captions, notes, acknowledgements, references, and licence text when present. Preserve the wording, including apparent source errors; flag unreadable passages rather than inventing text.
- Remove repeated running headers, page numbers, download stamps, and similar page furniture. Rejoin lines and paragraphs in reading order. Resolve soft line-break hyphens individually so genuine compound words and URLs remain intact. Normalize extraction-only glyphs such as private-use numerals.
- Use Markdown headings, lists, block quotes, tables, and footnotes where they make the original structure easier to read. Keep footnote calls attached to their sentences and all corresponding note text, including notes that continue on another page.
- Decide how to carry each meaningful visual: use Mermaid for a simple semantic diagram; embed an extracted or cropped image when visual fidelity matters; use a concise, located placeholder when either option would be misleading or disproportionately complex. Do not invent a visual when the PDF has none. In this vault, place source-derived image assets under `raw/assets/` and treat them as immutable once placed there.
- Put the Markdown at the requested location, or beside the PDF with the same stem if no location was specified. Link to the fresh online URL supplied for this conversion. Follow the user's link instructions exactly, including any request not to link the local PDF.

## Verify before delivery

- Compare the Markdown with the PDF page by page, checking that no text block, note, reference entry, table, or visual is missing or out of order. Extraction word counts or sequence comparisons can help find omissions, but do not replace visual review.
- Check section order, footnote calls and definitions, reference boundaries, broken words and URLs, unreadable characters, and accidental inclusion of page furniture. Correct extraction errors against the rendered original.
- Report any passage or visual that could not be faithfully transcribed. Leave the PDF untouched. Conversion alone does not authorize wiki ingestion, source archival, or deletion.
