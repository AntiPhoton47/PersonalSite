---
layout: single
title: "Sitemap"
permalink: /sitemap/
---

{% include base_path %}

A comprehensive overview of all content on this website. For search engines, an [XML version]({{ base_path }}/sitemap.xml) is available.

## Pages
{% for page in site.pages %}
- [{{ page.title }}]({{ page.url | relative_url }})
{% endfor %}

## Posts
{% for post in site.posts %}
- [{{ post.title }}]({{ post.url | relative_url }})
{% endfor %}
