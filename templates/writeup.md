# <img src="{{ resource.info.logo }}" width="100" height="100" alt="Resource Logo"> [{{ taggify(resource.info.name) }}]({{resource.info.url}})

{{ ' '.join(taggify(resource.info.tags)) }}


## About
- Type: {{ taggify(resource.type_name) }}
- Tags: {{ ' '.join(taggify(resource.info.tags)) }}
- Difficulty: {{ taggify(resource.info.difficulty) }}
- Status: {{ taggify(resource.info.status) }} 
- OS: {{ taggify(resource.info.os) }}
- Authors: {{ ' '.join(taggify(resource.info.authors)) }}
- Points: {{ taggify(resource.info.points) }}

## Description

{% if resource.info.description is none %}
Description not provided
{% else %}
{{ resource.info.description }}
{% endif %}


## Writeup
{% set require_vpn = ['stp', 'mch'] %}
{% if resource.type in require_vpn %}
> To attack the target machine, you must be on the same network.
> Connect to the Starting Point VPN using one of the following options: Pwnbox or OpenVPN
{% endif %}
```bash
export TARGET="{{ resource.about.targets[0] }}"
```

{% for task in resource.tasks %}
{{ task.to_markdown() }}
{% endfor %}
