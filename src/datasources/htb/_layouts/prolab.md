# <img src="{{ resource.metadata.logo }}" width="100" height="100" alt="Resource Logo"> [`{{ resource.metadata.title }}`]({{resource.metadata.url}})

{% if resource.metadata.description %}{{ resource.metadata.description }}{% endif %}

## Targets

> Entry point: **{{ resource.entry_point }}**

{% for tg in resource.targets %}
- [ ] [{{ tg.metadata.title }}](./targets/{{ tg.name }}/writeup.md)
{% endfor %}


## Tasks

{% for task in resource.tasks %}
{{ task.to_markdown() }}
{% endfor %}


