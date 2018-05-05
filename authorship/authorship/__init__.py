"""
Authorship — Stores a list of authors for each document.

The data is stored in the environment under the key ``authors``. It's a
dictionary, where the keys are the names of the documents and the values a list
of author names.

"""

import itertools

from docutils import nodes
from docutils.parsers.rst import directives
from sphinx.util.docutils import SphinxDirective
import sphinx.addnodes as addnodes


def comma_list(nodes_):
    """Return list of nodes seperated by `, ` text nodes."""
    elements = []

    if not nodes_:
        return []

    for node in nodes_:
        elements.append(node)
        elements.append(nodes.Text(', '))

    return elements[:-1]


class Author(SphinxDirective):
    """
    Store author information in the environment (``authors``).

    Append given author info to the list for the current document.

    From rst markup like::

        .. author:: YourName <YourURL/YourMail>

    """
    required_arguments = 1
    final_argument_whitespace = True

    def run(self):
        env = self.state.document.settings.env

        env.authors.setdefault(env.docname, [])
        env.authors[env.docname].append(self.arguments[0])

        return []


class Authors(SphinxDirective):
    """
    Output the list of authors for the document.

    Like: `Written by: author1 <mail@some.org>, author2 <site.org>`

    From rst markup like::

        .. authors::

    """
    def run(self):
        env = self.state.document.settings.env
        authors = env.authors.get(env.docname, [])

        if not authors:
            return [nodes.Text('Written by: Uberspace')]

        return [nodes.Text('Written by: ')] + comma_list(nodes.Text(a) for a in authors)


class allauthors(nodes.General, nodes.Element):
    """Maker node later to be replaced by list of all authors."""
    pass


class AllAuthors(SphinxDirective):
    """
    Outputs an ordered list of all authors, sorted by contribution count.

    From rst markup like::

        .. allauthors::

    """
    def run(self):
        return [allauthors('')]


def builder_inited(app):
    """Initialize environment."""
    app.builder.env.authors = {}


def purge_authors(app, env, docname):
    """Remove possible stale info for updated documents."""
    if not hasattr(env, 'authors'):
        return

    env.authors.pop(docname, None)


def process_authorlists(app, doctree, fromdocname):
    """Build list of authors sorted by contribution count."""
    env = app.builder.env
    authors = set(itertools.chain(*[authors for authors in env.authors.values()]))
    guides_by_author = {
        a: set(g for g, guide_authors in env.authors.items() if a in guide_authors)
        for a in authors
    }

    for node in doctree.traverse(allauthors):
        lst = nodes.bullet_list()

        for author in authors:
            lst_item = nodes.list_item()
            lst += lst_item
            lst_item += addnodes.compact_paragraph(text=author)

            lst_item += nodes.raw('', '<br>', format='html')

            links = []

            for guide in guides_by_author[author]:
                # I can't figure out a way to get the link and title from a page name..
                link = guide + '.html'
                title = guide.partition('_')[2].title()

                link_wrapper = addnodes.compact_paragraph()
                link_wrapper += nodes.reference(
                    '', '', nodes.Text(title), internal=True, refuri=link, anchorname=''
                )

                links.append(link_wrapper)

            for n in comma_list(links):
                lst_item += n

        node.replace_self([lst])


def setup(app):
    app.add_node(allauthors)

    directives.register_directive('author', Author)
    directives.register_directive('authors', Authors)
    directives.register_directive('allauthors', AllAuthors)

    app.connect('builder-inited', builder_inited)
    app.connect('env-purge-doc', purge_authors)
    app.connect('doctree-resolved', process_authorlists)

    return {
        'version': '1.0.0',
    }
