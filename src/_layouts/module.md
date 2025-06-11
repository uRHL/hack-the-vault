---
__type__: htb.mod
duration: 4 hours
metadata:
  authors:
  - 21y4d
  creation_date: 2025-05-19 18:04:39 +0200
  difficulty: Easy
  logo: https://academy.hackthebox.com/storage/modules/41/logo.png?t=1739540143
  rating: '4.8238'
  tags: [Defensive]
  title: JavaScript Deobfuscation
  url: https://academy.hackthebox.com/module/details/41
sections: {{ resource.sections.__len__() }} 
tier: '0'
---

{{ templater.backlink(resource) }}

# <a href="{{ resource.metadata.url }}"><img src="{{ resource.metadata.logo }}" width="100" height="100" alt="Resource Logo"> `{{ resource.metadata.title }}` </a>

{{ resource.description }}

## Index

{% for st in resource.sections %}{{ loop.index }}. [{{st.title}}](./{{ st.__file_name__ }})
{% endfor%}

## About

{{ resource.summary }}


