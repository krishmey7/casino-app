from django import template

register = template.Library()

@register.filter
def get_item(dictionary, key):
    """Récupère une valeur dans un dictionnaire avec une clé dynamique"""
    if dictionary is None:
        return None
    return dictionary.get(key)

@register.filter
def str_concat(a, b):
    """Concatène deux chaînes de caractères"""
    return f"{a}{b}"

@register.filter
def reverse_index(value, max_val):
    """Inverse un index (0-9 devient 9-0)"""
    return max_val - value
