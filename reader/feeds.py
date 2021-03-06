from mimetypes import guess_type
from typing import TYPE_CHECKING, Iterable, Optional

from django.conf import settings
from django.contrib.syndication.views import Feed
from django.utils import timezone as tz
from django.utils.feedgenerator import Atom1Feed

from .models import Chapter, Series

if TYPE_CHECKING:  # pragma: no cover
    from datetime import datetime
    from django.http import HttpRequest

_max = settings.CONFIG['MAX_RELEASES']


class LibraryRSS(Feed):
    """RSS feed for the series library."""
    ttl = 600
    link = '/reader/'
    description = 'Updates when a new series is added'
    author_name = settings.CONFIG['NAME']
    title = f'Library - {author_name}'
    item_guid_is_permalink = True

    def items(self) -> Iterable[Series]:
        """
        Get an iterable of the feed's items.

        :return: An iterable of ``Series`` objects.
        """
        return Series.objects.order_by('-created')[:_max]

    def item_description(self, item: Series) -> str:
        """
        Get the description of the item.

        :param item: A ``Series`` object.

        :return: The description of the series.
        """
        return item.description.replace('\n', '<br/>')

    def item_categories(self, item: Series) -> Iterable[str]:
        """
        Get the categories of the item.

        :param item: A ``Series`` object.

        :return: The names of the series' categories.
        """
        return item.categories.values_list('name', flat=True)

    def item_pubdate(self, item: Series) -> 'datetime':
        """
        Get the publication date of the item.

        :param item: A ``Series`` object.

        :return: The date the series was created.
        """
        return item.created

    def item_updateddate(self, item: Series) -> 'datetime':
        """
        Get the update date of the item.

        :param item: A ``Series`` object.

        :return: The date the series was modified.
        """
        return item.modified

    def item_enclosure_url(self, item: Series) -> Optional[str]:
        """
        Get the enclosure URL of the item.

        :param item: A ``Series`` object.

        :return: The URL of the series' cover image, if available.
        """
        if not item.cover:
            return None
        url = item.cover.url
        return url if url[:4] == 'http' else \
            f'http://{settings.CONFIG["DOMAIN"]}{url}'

    def item_enclosure_length(self, item: Series) -> Optional[int]:
        """
        Get the enclosure length of the item.

        :param item: A ``Series`` object.

        :return: The size of the series' cover image, if available.
        """
        return item.cover.size if item.cover else None

    def item_enclosure_mime_type(self, item: Series) -> Optional[str]:
        """
        Get the enclosure type of the item.

        :param item: A ``Series`` object.

        :return: The mime type of the series' cover image, if available.
        """
        return guess_type(item.cover.path)[0] if item.cover else None


class LibraryAtom(LibraryRSS):
    """Atom feed for the series library."""
    feed_type = Atom1Feed
    subtitle = LibraryRSS.description


class ReleasesRSS(Feed):
    """RSS feed for chapter releases."""
    ttl = 600
    author_name = settings.CONFIG['NAME']
    item_guid_is_permalink = True

    def get_object(self, request: 'HttpRequest', slug:
                   Optional[str] = None) -> Optional[Series]:
        """
        Get a ``Series`` object from the request.

        :param request: The original request.
        :param slug: The slug of the series.

        :return: The series that has the given slug,
                 or ``None`` if the slug is ``None``.
        """
        if slug is None:
            return None
        return Series.objects.prefetch_related('chapters').get(slug=slug)

    def link(self, obj: Optional[Series]) -> str:
        """
        Get the link of the feed's page.

        :param obj: The object of the feed.

        :return: The URL of the series, or the home page.
        """
        return obj.get_absolute_url() if obj else '/'

    def title(self, obj: Optional[Series]) -> str:
        """
        Get the title of the feed.

        :param obj: The object of the feed.

        :return: The title of the series, or ``Releases``.
        """
        title = obj.title if obj else 'Releases'
        return f'{title} - {self.author_name}'

    def description(self, obj: Optional[Series]) -> str:
        """
        Get the description of the feed.

        :param obj: The object of the feed.

        :return: A description with the title of the series, if available.
        """
        if obj is None:
            return 'Updates when a new chapter is added'
        return f'Updates when a new chapter of {obj.title} is added'

    def items(self, obj: Optional[Series]) -> Iterable[Chapter]:
        """
        Get an iterable of the feed's items.

        :param obj: The object of the feed.

        :return: An iterable of ``Chapter`` objects.
        """
        return getattr(obj, 'chapters', Chapter.objects) \
            .filter(published__lte=tz.now()).order_by('-published')[:_max]

    def item_description(self, item: Chapter) -> str:
        """
        Get the description of the item.

        :param item: A ``Chapter`` object.

        :return: The ``Chapter`` object as a string.
        """
        desc = str(item)
        if settings.CONFIG['ALLOW_DLS']:
            domain = settings.CONFIG["DOMAIN"]
            url = item.get_absolute_url()[:-1] + '.cbz'
            desc = f'<a href="http://{domain}{url}">{desc}</a>'
        return desc

    def item_pubdate(self, item: Chapter) -> 'datetime':
        """
        Get the publication date of the item.

        :param item: A ``Chapter`` object.

        :return: The date the chapter was published.
        """
        return item.published

    def item_updateddate(self, item: Chapter) -> 'datetime':
        """
        Get the update date of the item.

        :param item: A ``Chapter`` object.

        :return: The date the chapter was modified.
        """
        return item.modified


class ReleasesAtom(ReleasesRSS):
    """Atom feed for chapter releases."""
    feed_type = Atom1Feed
    subtitle = ReleasesRSS.description


__all__ = ['LibraryRSS', 'LibraryAtom', 'ReleasesRSS', 'ReleasesAtom']
