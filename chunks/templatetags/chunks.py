from django import template

try:
    # noinspection PyUnresolvedReferences
    from django.db.models.loading import get_model
except ImportError:
    # noinspection PyUnresolvedReferences
    from django.db.models import get_model

from django.core.cache import cache

register = template.Library()

Chunk = get_model('chunks', 'chunk')
CACHE_PREFIX = "chunk_"


def do_get_chunk(parser, token):
    # split_contents() knows not to split quoted strings.
    tokens = token.split_contents()
    if len(tokens) == 2:
        tag_name, key = tokens
        cache_time = 0
    elif len(tokens) == 3:
        tag_name, key, cache_time = tokens
    else:
        raise template.TemplateSyntaxError, "%r tag should have either 2 or 3 arguments" % (tokens[0],)
    # Check to see if the key is properly double/single quoted
    if not (key[0] == key[-1] and key[0] in ('"', "'")):
        raise template.TemplateSyntaxError, "%r tag's argument should be in quotes" % tag_name
    # Send key without quotes and caching time
    return ChunkNode(key[1:-1], cache_time)


class ChunkNode(template.Node):
    def __init__(self, key, cache_time=0):
        self.key = key
        self.cache_time = cache_time
    
    def render(self, context):
        try:
            cache_key = CACHE_PREFIX + self.key
            c = cache.get(cache_key)
            if c is None:
                c = Chunk.objects.get(key=self.key)
                cache.set(cache_key, c, int(self.cache_time))
            content = c.content
        except Chunk.DoesNotExist:
            content = ''
        return content
        
register.tag('chunk', do_get_chunk)
