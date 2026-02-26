---
layout: single
title: "Sitemap"
permalink: /sitemap/
---

You can also view the machine-readable XML sitemap [here]({{ "/sitemap.xml" | relative_url }}).

## Pages
{% for page in site.pages %}
- [{{ page.title }}]({{ page.url | relative_url }})
{% endfor %}

## Posts
{% for post in site.posts %}
- [{{ post.title }}]({{ post.url | relative_url }})
{% endfor %}
