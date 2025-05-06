# <img src="{{ lab.info.logo }}" width="100" height="100" alt="Resource Logo"> [`{{ lab.info.name }}`]({{lab.info.url}})

{{ ' '.join(taggify(lab.info.tags)) }}


## About

- Type: `{{ lab.type_name }}`
- Tags: {{ ' '.join(taggify(lab.info.tags)) }}
- Difficulty: `{{ lab.info.difficulty }}`
- Authors: {{ ' '.join(taggify(lab.info.authors)) }}
- Points: `{{ lab.info.points }}`

## Description

{% if lab.info.description is none %}
Description not provided
{% else %}
{{ lab.info.description }}
{% endif %}

## Targets

> Entry point: **{{ lab.entry_point }}**

{% for tg in lab.about.targets %}
- [ ] [{{ tg.info.name }}](./targets/{{ tg.info.name }}/writeup.md)
{% endfor %}


## Tasks

{% for task in lab.tasks %}
{{ task.to_markdown() }}
{% endfor %}


