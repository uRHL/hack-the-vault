{{ templater.backlink(resource) }}

# <img src="{{ resource.metadata.logo }}" width="100" height="100" alt="Resource Logo"> [{{ resource.metadata.title }}]({{resource.metadata.url}})

{% if resource.metadata.description %}{{ resource.metadata.description }}{% endif %}

## Writeup

{% set require_vpn = ['htb.stp', 'htb.mch'] %}
{% if resource.type in require_vpn %}
> To attack the target machine, you must be on the same network.
> Connect to the Starting Point VPN using one of the following options: Pwnbox or OpenVPN
{% endif %}
```bash
export TARGET="{{ resource.metadata.targets[0] }}"
```


{% for task in resource.tasks %}
{% include 'task.md' %}
{% endfor %}
