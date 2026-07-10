---
hide:
    - navigation
    - toc
    - title
---

<!-- 
# Copyright (c) 2025-2026 Mark Buckwell and contributors
# SPDX-License-Identifier: MIT
-->

[:material-file-pdf-box: PDF](site_documentation.pdf){ .md-button target="_blank" style="float: right; margin-left: 15px;" .web-only}

<!-- Hide heading 1 on the page as hide: title does not seem to work -->
<style> .md-typeset h1 { display: none; } </style>
<!-- We still need a title set for the next/previous page navigation
     to work, so we set it here but hide it from the page.
-->
# Cover Page {.unnumbered .unlisted .hidden}

<!--
/*================== TITLE PAGE SURREY GITLAB ==================*/ 
-->
{% if is_surrey %}

<br>
<br>
<br>
![](assets/cover-centre-logo-black.png#only-light){ width="40%" style="display: block; margin: 0 auto;" }
![](assets/cover-centre-logo-white.png#only-dark){ width="40%" style="display: block; margin: 0 auto;" }

<!-- the different title line use styles defined in the extras.css file -->
<p class="title-ctr-b4">
Faculty of Engineering and Physical Sciences<br>
School of Computer Science and Electronic Engineering
</p>

<p class="title-ctr-4"> MSc programmes in Computer Science</p>


<p class="title-ctr-b4">module_id - module_name</p>

<p class="title-ctr-b4">{{ site_name }}</p>

<!--
/*================== TITLE PAGE GITHUB OR OTHER GITLAB ==================*/
-->
{% else %}

<br>
<br>
<br>
![](assets/logo_default_black.png#only-light){ width="15%" style="display: block; margin: 0 auto;" }
![](assets/logo_default_white.png#only-dark){ width="15%" style="display: block; margin: 0 auto;" }

<!-- the different title line use styles defined in the extras.css file -->
<p class="title-ctr-b4">
Crested Eagle Labs</p>

<p class="title-ctr-b4">
University of the World</p>

<p class="title-ctr-4">
Research programmes in Cyber Security</p>

<p class="title-ctr-b4">{{ site_name }}</p>
{% endif %}

<br>
<br>
<br>
<br>


<!--
  In using this style, it's been applied to multiple lines using the line break
  Fill in your own name and the date the document is released.
-->
<p class="title-left-5">
Author: Insert Name Here
<br>
Date: Submission Date
</p>

<!-- Automated word count of the PDF body content, filled in at PDF build
     time by build_pdf.py. Delete this line if you don't want a word
     count shown on the cover page. -->
<p class="pdf-only">Word count: {WORDCOUNT}</p>

<!-- Automated repository URL, filled in at PDF build time by
     build_pdf.py. Delete this line if you don't want the repository
     link shown on the cover page. -->
<p class="pdf-only">Repo: {REPOURL}</p>
