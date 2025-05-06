# Module ({{mod.tier}}): [`{{ mod.info.name }}`]({{mod.info.url}}) 

![logo]({{mod.info.logo}})

{{mod.info.description}}

## Info

- Tags: {{ ' '.join(taggify(mod.info.tags)) }}
- Difficulty: `{{ mod.info.difficulty }}`
- Tier: `{{mod.tier}}`
  - Cost: `{{mod.cost}}`
  - Points: `{{mod.info.points}}`
- Duration: `{{ mod.duration }}`
- Rating: `{{ mod.about.rating }}`
- Authors: {{ ' '.join(taggify(mod.info.authors)) }}

## Index
{% for st in mod.sections %}
{{ loop.index}}. [ ] [{{loop.index}}. {{st.title }}](./{{loop.index}}_{{st.name}}.md)
{% endfor %}


## Summary

{{ mod.summary }}
