from jinja2 import Template

template = Template('''
{% if exam.start_date and exam.start_date > current_time %}
    Starts: {{ exam.start_date.replace('T', ' ') }}
{% elif exam.end_date and exam.end_date < current_time %}
    Ended: {{ exam.end_date.replace('T', ' ') }}
{% else %}
    Started!
{% endif %}
''')

# Test with None
result = template.render(exam={'start_date': None, 'end_date': None}, current_time='2026-05-21T00:13')
print("Result with None:", result.strip())

# Test with string
result2 = template.render(exam={'start_date': '2026-05-22T00:00', 'end_date': None}, current_time='2026-05-21T00:13')
print("Result with string:", result2.strip())
