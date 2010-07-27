from django.core.management.base import BaseCommand
from optparse import make_option

class Command(BaseCommand):
    option_list = BaseCommand.option_list + (
        make_option('-e', '--exclude', dest='exclude',action='append', default=[],
            help='''Models to exclude (use multiple --exclude to exclude multiple models).
            The default settings include Post, Category, Tag and Comment'''),
        make_option(None, '--with-spam', action="store_true", dest='keep_spam', default=False,
            help='Import the spam comments.'),
        make_option(None, '--without-spam', action="store_false", dest='keep_spam',
            help='Do not import the spam comments.'),
        make_option(None, '--with-pingpack', action="store_true", dest='keep_pingback', default=False,
            help='Import the pingbacks.'),
        make_option(None, '--without-pingback', action="store_false", dest='keep_pingback',
            help='Do not import the pingbacks.'),
        make_option('-m', '--markup', default="wpmarkup", dest='markup', 
            help='Which markup is used, default is wpmarkup, note: you need to install wpmarkup.'),
        make_option('-f', '--from', default='wordpress', dest='other_blog',
            help='Blog system to import, default is wordpress.'),
        )
    help = 'Import the data from other blog system.'

    args = 'exported_data'

    def handle(self, exported_data, **options):
        other_blog = options.get('other_blog', 'wordpress')
        if other_blog == 'wordpress':
            return self.handle_wordpress(exported_data, **options)
        else:
            print "Only wordpress is supported now."

    def handle_wordpress(self, exported_data, **options):

        excludes = options.get('exclude', [])
        keep_spam = options.get('keep_spam', False)
        keep_pingback = options.get('keep_pingback', False)
        body_markup = options.get('markup')
        if keep_pingback:
            print "--with-pingback has not been implemented yet."
            keep_pingback = False

        from django.conf import settings
        from xml.etree import ElementTree as ET
        from datetime import datetime
        from urlparse import urlparse
        from django.contrib.contenttypes.models import ContentType
        from django.contrib.sites.models import Site
        from django.contrib.auth.models import User
        from django.contrib.redirects.models import Redirect
        from django.contrib.comments import Comment
        from django.utils.encoding import force_unicode
        from basic.blog.models import Post, Category
        from tagging.models import Tag, TaggedItem
        
        def translate_status(status):
            return [0, 'draft', 'publish', 'private'].index(status)

        def translate_comment_status(status):
            return status == 'open'

        tree = ET.parse(exported_data)
        qnames = {
                "wp": "http://wordpress.org/export/1.0/",
                "dc": "http://purl.org/dc/elements/1.1/",
                "content": "http://purl.org/rss/1.0/modules/content/",
                "excerpt": "http://wordpress.org/export/1.0/excerpt/",
        }
        site = Site.objects.get(id=settings.SITE_ID)

        # category
        if 'Category' not in excludes:
            for category in tree.findall("channel/{%(wp)s}category" % qnames):
                title = category.find('{%(wp)s}cat_name' % qnames).text
                slug = category.find('{%(wp)s}category_nicename' % qnames).text
                c, created = Category.objects.get_or_create(title=title, slug=slug)
                if created:
                    c.save()
                    print "Create category %s " % title

        if 'Tag' not in excludes:
            for tag in tree.findall("channel/{%(wp)s}tag" % qnames):
                title = tag.find('{%(wp)s}tag_name' % qnames).text.lower()
                slug = tag.find('{%(wp)s}tag_slug' % qnames).text
                t, created = Tag.objects.get_or_create(name=title)
                if created:
                    t.save()
                    print "Create tag %s " % title
            
        if 'Post' not in excludes:
            for post in tree.findall("channel/item" % qnames):
                # TODO: add transcation support
                title = post.find('title').text
                post_type = post.find("{%(wp)s}post_type" % qnames).text
                if post_type == 'page':
                    print "Ignore page %s " % title

                slug = post.find("{%(wp)s}post_name" % qnames).text
                author, created = User.objects.get_or_create(username=post.find("{%(dc)s}creator" % qnames).text)
                if created:
                    author.save()

                body = post.find("{%(content)s}encoded" % qnames).text or ''
                tease = post.find("{%(excerpt)s}encoded" % qnames).text or ''
                status = translate_status(post.find("{%(wp)s}status" % qnames).text)
                allow_comments = translate_comment_status(post.find("{%(wp)s}comment_status" % qnames).text)
                publish = datetime.strptime(post.find("pubDate" % qnames).text, '%a, %d %b %Y %H:%M:%S +0000')
                # use GMT?
                created_date = datetime.strptime(post.find("{%(wp)s}post_date" % qnames).text, '%Y-%m-%d %H:%M:%S')
                p, created = Post.objects.get_or_create(title=title, slug=slug, author=author, body=body, tease=tease,
                        status=status, allow_comments=allow_comments, publish=publish, created=created_date, body_markup_type=body_markup)
                if created:
                    p.save()
                    old_path = urlparse(post.find('link').text).path
                    new_path = p.get_absolute_url()
                    Redirect.objects.create(site=site, old_path=old_path, new_path=new_path)

                    print "Create post %s " % title
                else:
                    print "Get post %s " % title

                cat_tag = post.findall("category")
                if 'Category' not in excludes:
                    for cat in cat_tag:
                        if cat.attrib.get('domain', '') != 'category':
                            continue
                        cat_name = cat.text
                        slug = cat.attrib.get('nicename', cat_name.lower())
                        c, created = Category.objects.get_or_create(title=cat_name, slug=slug)
                        if created:
                            c.save()
                        print "    add category %s" % cat_name
                        p.categories.add(c)

                if 'Tag' not in excludes:
                    tags = filter(lambda x:    x.attrib.get('domain') == 'tag' and x.attrib.get('nicename') != None, cat_tag)
                    t = ' '.join([x.attrib['nicename'] for x in tags])
                    p.tags = t
                    print "    add tag %s" % t

                p.save()

                if 'Comment' not in excludes:
                    for comment in post.findall("{%(wp)s}comment" % qnames):
                        comment_approved = comment.find("{%(wp)s}comment_approved" % qnames).text
                        if comment_approved == 'spam' and keep_spam == False:
                            continue
                        comment_type = comment.find("{%(wp)s}comment_type" % qnames).text
                        if comment_type == 'pingback' and keep_pingback == False:
                            continue
                        comment_content = comment.find("{%(wp)s}comment_content" % qnames).text
                        if comment_content == None or comment_content == '':
                            continue

                        user_id =    comment.find("{%(wp)s}comment_user_id" % qnames).text
                        user_name = comment.find("{%(wp)s}comment_author" % qnames).text 
                        user_email = comment.find("{%(wp)s}comment_author_email" % qnames).text or ''
                        user_url = comment.find("{%(wp)s}comment_author_url" % qnames).text or ''
                        submit_date = comment.find("{%(wp)s}comment_date" % qnames).text
                        ip_address = comment.find("{%(wp)s}comment_author_IP" % qnames).text
                        submit_date = datetime.strptime(comment.find("{%(wp)s}comment_date" % qnames).text, '%Y-%m-%d %H:%M:%S')
                        comment_approved = comment.find("{%(wp)s}comment_approved" % qnames).text
                        is_public = comment_approved == '1'
                        is_removed = comment_approved == 'spam'


                        # Create the comment
                        #import pdb; pdb.set_trace()
                        c, created = Comment.objects.get_or_create(
                                content_type=ContentType.objects.get_for_model(p), 
                                object_pk=p._get_pk_val(), site=site,
                                user_name=user_name,user_email=user_email, user_url=user_url, 
                                comment=comment_content, submit_date=submit_date, ip_address=ip_address, 
                                is_public=is_public, is_removed=is_removed)
                        if created:
                            c.save()
                            print "Create comment: %s" % force_unicode(c._get_pk_val())
