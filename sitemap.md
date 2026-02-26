---
layout: single
title: "Sitemap"
permalink: /sitemap/
---

You can also view the machine-readable XML sitemap [here]({{ "/sitemap.xml" | relative_url }}).

## Pages
{% assign pages = site.pages
  | where_exp: "p", "p.title"
  | where_exp: "p", "p.url != nil"
  | sort: "url" %}

{% for p in pages %}
{% if p.sitemap != false and p.url != "/sitemap.xml" and p.url != "/feed.xml" %}
- [{{ p.title }}]({{ p.url | relative_url }})
{% endif %}
{% endfor %}

## Posts
{% for post in site.posts %}
{% if post.sitemap != false %}
- [{{ post.title }}]({{ post.url | relative_url }}) — {{ post.date | date: "%B %-d, %Y" }}
{% endif %}
{% endfor %}
