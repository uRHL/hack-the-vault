{{ templater.backlink(resource) }}

# {{ resource.name[0].upper() +  resource.name[1:]}}

Description of what is stored here


## Index

{% for item in (VAULT_DIR / resource).glob('[a-z]*') if item.is_dir() %}
-[{{ item.name[0].upper() + item.name[1:] }}](./{{ item.name }}/README.md){% else %} No resources yet
{% endfor %}


