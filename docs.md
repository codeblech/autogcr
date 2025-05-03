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

- todo

  - cli
  - more solvers
  - after turning in an assignment, check presence of 'unsubmit' button to verify that the assignment was turned in
  - use numba to speed up the image generation code