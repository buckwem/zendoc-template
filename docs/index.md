---
hide:
    - navigation
    - toc
    - title
---

<!-- 
# Copyright (c) 2025-2026 Mark Buckwell and contributors
# SPDX-License-Identifier: MIT
# All contributions are certified under the DCO
-->

[:material-file-pdf-box: PDF](site_documentation.pdf){ .md-button target="_blank" style="float: right; margin-left: 15px;"}

<!-- Hide heading 1 on the page as hide: title does not seem to work -->
<style> .md-typeset h1 { display: none; } </style>
<!-- We still need a title set for the next/previous page navigation
     to work, so we set it here but hide it from the page.
-->
# Cover Page

<!--
/*================== TITLE PAGE SURREY GITLAB ==================*/ 
-->
{% if is_surrey %}


<!-- The align attribute does not support centering.
     so we use a blank caption to centre an image.
     We also suppport swapping of the logo to 
     support a dark and light theme
-->
<br>
<br>

![](assets/cover-centre-logo-black.png#only-light){ width="40%" style="display: block; margin: 0 auto;" }
![](assets/cover-centre-logo-white.png#only-dark){ width="40%" style="display: block; margin: 0 auto;" }

<br>
<br>

<!-- the different title line use styles defined in the extras.css file -->
<p class="title-ctr-b4">
Faculty of Engineering and Physical Sciences<br>
School of Computer Science and Electronic Engineering
</p>

<p class="title-ctr-4"> MSc programmes in Computer Science</p>


<p class="title-ctr-b4">module_id - module_name</p>

<!--
/*================== TITLE PAGE GITHUB OR OTHER GITLAB ==================*/
-->
{% else %}

![](assets/logo_default_black.png#only-light){ width="10%" style="display: block; margin: 0 auto;" }
![](assets/logo_default_white.png#only-dark){ width="60%" style="display: block; margin: 0 auto;" }

<!-- the different title line use styles defined in the extras.css file -->
<p class="title-ctr-b4">
Crested Eagle Labs</p>

<p class="title-ctr-b4">
University of the World</p>

<p class="title-ctr-4">
Research programmes in Cyber Security</p>
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
