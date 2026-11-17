# Typst documentation

Compile the document from the repository root so Typst can read the profiling JSON under `database/`:

```sh
typst compile --root . projectInstructions/typst/main.typ projectInstructions/typst/SOEN363_Phase2_Report.pdf
```

For automatic recompilation when a source file changes, use:

```sh
typst watch --root . projectInstructions/typst/main.typ projectInstructions/typst/SOEN363_Phase2_Report.pdf
```

`main.typ` assembles the modular report, including Section 2, Sections 3–3.2, the reserved Appendix A, field-level Appendix B, and the ICD-9 reference Appendix C. Task 1, Sections 3 and 3.1–3.2 import existing JSON/CSV resources with Typst's native readers during compilation. `styles.typ` defines reusable table styling and helpers. User-written explanations remain placeholders.

`appendix-b.typ` generates one dynamic field-level table per source, with entity groups visually separated. `appendix-c.typ` reads the supplied ICD-9 CSV without converting its code strings.
