# <img src="{{ track.info.logo }}" width="100" height="100" alt="Resource Logo"> [`{{ track.info.name }}`]({{track.info.url}})

{{ ' '.join(taggify(track.info.tags)) }}


## About

- Type: `{{ track.type_name }}`
- Tags: {{ ' '.join(taggify(track.info.tags)) }}
- Difficulty: `{{ track.info.difficulty }}`
- Status: `{{ track.info.status }}`
- Authors: {{ ' '.join(taggify(track.info.authors)) }}
- Points: `{{ track.info.points }}`

## Description

{% if track.info.description is none %}
Description not provided
{% else %}
{{ track.info.description }}
{% endif %}

## Index

{% for task in track.tasks %}
{{loop.index}}. [ ] [{{loop.index}}. {{ task.type_name }}: {{ task.info.name }}](../../../{{ task.path }}/index.md)
{% endfor %}
