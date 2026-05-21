---
hide:
    - navigation
    - toc
    - title
---

<!-- Hide heading 1 on the page as hide: title does not work -->
<style>
  .md-typeset h1 {
    display: none;
  }
</style>

<!-- The align attribute does not support centering.
     so we use a blank caption to centre an image.
     We also suppport swapping of the logo to 
     support a dark and light theme
-->

![](./assets/cover-centre-logo-black.png#only-light){ width="40%" }
![](./assets/cover-centre-logo-white.png#only-dark){ width="40%" }
/// caption

///

<!-- the different title line use styles defined in the extras.css file -->

<p class="title-ctr-b4">
Faculty of Engineering and Physical Sciences<br>
School of Computer Science and Electronic Engineering</p>

<p class="title-ctr-4">
MSc programmes in Computer Science</p>

<p class="title-ctr-b2">module_id – module_name</p>

<br>
<br>
<br>
<br>

<!--
  In using this style, it's been applied to multiple lines using the line break
  Fill in your own name and the date the document is released.
-->
<p class="title-left-5">
Author: Insert Name Here<br>
Date: Submission Date
</p>
