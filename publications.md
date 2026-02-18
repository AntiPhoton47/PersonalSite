---
title: "Publications"
permalink: /publications/
---

## Selected publications
(Replace these with your own. Edit `_data/publications.yml`.)

{% for pub in site.data.publications %}
### {{ pub.title }}
**{{ pub.authors }}**  
*{{ pub.venue }}* ({{ pub.year }})  
{% if pub.links %}
{% for link in pub.links %}
- [{{ link.label }}]({{ link.url }})
{% endfor %}
{% endif %}
{% endfor %}

---

## BibTeX
- [Download BibTeX](/assets/files/publications.bib)
