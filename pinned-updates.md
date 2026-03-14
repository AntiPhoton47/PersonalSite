---
title: "Pinned Updates"
permalink: /pinned-updates/
author_profile: false
toc: false
---

These are the major updates and entry points currently highlighted on the homepage.

{% for banner in site.data.site_highlights.homepage_banners %}
  <article class="pinned-update pinned-update--full">
    <p class="section-kicker">{{ banner.label }}</p>
    <div class="pinned-update__body">
      <div>
        <h2>{{ banner.title }}</h2>
        <p>{{ banner.text }}</p>
      </div>
      {% if banner.links %}
      <div class="pinned-update__links">
        {% for link in banner.links %}
          <a href="{{ link.url | relative_url }}">{{ link.label }}</a>
        {% endfor %}
      </div>
      {% endif %}
    </div>
  </article>
{% endfor %}
