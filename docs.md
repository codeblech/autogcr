when switching google accounts, you need to delete the `user` directory in the root directory.


quirks:
- in an assignment, we might need a diagram
  - llm should decide whether to draw a diagram or not
  - if yes, llm should return mermaid output. we can render the mermaid output, then embed it in the solution doc.
  - if no, llm should just output the text

- we might need to show output of code as a screenshot
  - llm should decide whether to show output of code as a screenshot or not
  - white text on a black background with some syntax highlighting looks like a screenshot
  - we can use `pygments` to get the syntax highlighting

- gemini doesn't support docx files, so we need to convert them first. docx can contain images, so we can't use markdown. we need to convert them to pdf or images.

- todo
  - cli
  - if attachment is docx, we should convert it to pdf first
  - after turning in an assignment, check presence of 'unsubmit' button to verify that the assignment was turned in
  - Markdown2docx can't covert code blocks to docx, so we should use a different library