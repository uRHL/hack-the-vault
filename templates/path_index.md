# {{path.type_name}}: [`{{ path.info.name }}`]({{path.info.url}}) 

![logo]({{path.info.logo}})

{{path.info.description}}

## Info

- Difficulty: `{{path.info.difficulty}}`
- Tier: {{ ' '.join(taggify(path.tier)) }}
- Cost: `{{path.cost}}`
- Duration: `{{path.duration}}`
- Sections: `{{path.sections}}`
- Status: `{{path.status}}`
- Authors: {{ ' '.join(taggify(path.info.authors)) }}
- Points: `{{path.info.points}}`

## Index
{% for mod in path.modules %}
{{loop.index}}. [ ] [{{loop.index}}. {{ mod.info.name }}](../../../{{ mod.path }}/index.md)
{% endfor %}

