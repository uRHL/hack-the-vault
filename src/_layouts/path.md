---
user: yml
---
{{ templater.backlink(resource) }}

# [`{{ resource.metadata.title }}`]({{resource.metadata.url}}) 

![logo]({{resource.metadata.logo}})

{% if resource.metadata.description %}{{ resource.metadata.description }}{% endif %}

## Info
__type__: resource.__type__
//- Tier: {{ ' '.join(resource.tier) }}
  //- Cost: `{{resource.cost}}`
  //- Duration: `{{resource.duration}}`
//- Sections: `{{resource.sections}}`
//- Points: `{{resource.metadata.points}}`
- Difficulty: `{{resource.metadata.difficulty}}`
- Status: `{{resource.status}}`
- Authors: {{ ' '.join(resource.metadata.authors) }}

## Index

{% for st in resource.sections %}
{{loop.index}}. [ ] [{{loop.index}}. {{ st.metadata.title }}](/{{ st.path }}/README.md)
{% endfor %}

