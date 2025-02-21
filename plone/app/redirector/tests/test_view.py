import unittest
from plone.app.redirector.tests.base import RedirectorTestCase

from zope.component import getUtility, getMultiAdapter
from plone.app.redirector.interfaces import IRedirectionStorage


class TestRedirectorView(RedirectorTestCase):
    """Ensure that the redirector view behaves as expected.
    """

    def afterSetUp(self):
        self.loginAsPortalOwner()
        self.portal.invokeFactory('Folder', 'testfolder')
        self.folder = self.portal.testfolder
        self.storage = getUtility(IRedirectionStorage)

    def view(self, context, actual_url, query_string=''):
        request = self.app.REQUEST
        request['ACTUAL_URL'] = actual_url
        request['QUERY_STRING'] = query_string
        return getMultiAdapter((context, request), name='plone_redirector_view')

    def test_attempt_redirect_with_known_url(self):
        fp = '/'.join(self.folder.getPhysicalPath())
        fu = self.folder.absolute_url()
        self.storage.add(fp + '/foo', fp + '/bar')
        view = self.view(self.portal, fu + '/foo')
        self.assertEquals(True, view.attempt_redirect())
        self.assertEquals(301, self.app.REQUEST.response.getStatus())
        self.assertEquals(fu + '/bar', self.app.REQUEST.response.getHeader('location'))

    def test_attempt_redirect_with_known_url_and_template(self):
        fp = '/'.join(self.folder.getPhysicalPath())
        fu = self.folder.absolute_url()
        self.storage.add(fp + '/foo', fp + '/bar')
        view = self.view(self.portal, fu + '/foo/view')
        self.assertEquals(True, view.attempt_redirect())
        self.assertEquals(301, self.app.REQUEST.response.getStatus())
        self.assertEquals(fu + '/bar/view', self.app.REQUEST.response.getHeader('location'))

    def test_attempt_redirect_with_known_url_and_view_with_part(self):
        fp = '/'.join(self.folder.getPhysicalPath())
        fu = self.folder.absolute_url()
        self.storage.add(fp + '/foo', fp + '/bar')
        view = self.view(self.portal, fu + '/foo/@@view/part')
        self.assertEquals(True, view.attempt_redirect())
        self.assertEquals(301, self.app.REQUEST.response.getStatus())
        self.assertEquals(fu + '/bar/@@view/part', self.app.REQUEST.response.getHeader('location'))

    def test_attempt_redirect_with_unknown_url(self):
        fp = '/'.join(self.folder.getPhysicalPath())
        fu = self.folder.absolute_url()
        view = self.view(self.portal, fu + '/foo')
        self.assertEquals(False, view.attempt_redirect())
        self.assertNotEquals(301, self.app.REQUEST.response.getStatus())

    def test_attempt_redirect_with_quoted_url(self):
        fp = '/'.join(self.folder.getPhysicalPath())
        fu = self.folder.absolute_url()
        self.storage.add(fp + '/foo', fp + '/bar')
        view = self.view(self.portal, fu + '/foo/baz%20quux')
        self.assertEquals(True, view.attempt_redirect())
        self.assertEquals(301, self.app.REQUEST.response.getStatus())
        self.assertEquals(fu + '/bar/baz%20quux', self.app.REQUEST.response.getHeader('location'))

    def test_attempt_redirect_with_query_string(self):
        fp = '/'.join(self.folder.getPhysicalPath())
        fu = self.folder.absolute_url()
        self.storage.add(fp + '/foo?blah=blah', fp + '/bar')
        view = self.view(self.portal, fu + '/foo','blah=blah')
        self.assertEquals(True, view.attempt_redirect())
        self.assertEquals(301, self.app.REQUEST.response.getStatus())
        self.assertEquals(fu + '/bar', self.app.REQUEST.response.getHeader('location'))

    def test_attempt_redirect_appending_query_string(self):
        fp = '/'.join(self.folder.getPhysicalPath())
        fu = self.folder.absolute_url()
        self.storage.add(fp + '/foo', fp + '/bar')
        view = self.view(self.portal, fu + '/foo', 'blah=blah')
        self.assertEquals(True, view.attempt_redirect())
        self.assertEquals(301, self.app.REQUEST.response.getStatus())
        self.assertEquals(fu + '/bar?blah=blah', self.app.REQUEST.response.getHeader('location'))

    def test_find_first_parent_found_leaf(self):
        self.folder.invokeFactory('Folder', 'f1')
        fu = self.folder.absolute_url()
        view = self.view(self.portal, fu + '/f1/p1')
        obj = view.find_first_parent()
        self.assertEquals(fu + '/f1', obj.absolute_url())

    def test_find_first_parent_found_node(self):
        self.folder.invokeFactory('Folder', 'f1')
        fu = self.folder.absolute_url()
        view = self.view(self.portal, fu + '/f1/p1/p2')
        obj = view.find_first_parent()
        self.assertEquals(fu + '/f1', obj.absolute_url())

    def test_find_first_parent_not_found(self):
        view = self.view(self.portal, '/foo/f1/p1/p2')
        self.assertEquals(None, view.find_first_parent())

    def test_search_leaf(self):
        self.folder.invokeFactory('Folder', 'f1')
        self.folder.invokeFactory('Folder', 'f2')
        self.folder.f1.invokeFactory('Document', 'p1')
        self.folder.f1.invokeFactory('Document', 'p2')
        fu = self.folder.absolute_url()
        view = self.view(self.portal, fu + '/f2/p1')
        urls = sorted([b.getURL() for b in view.search_for_similar()])
        self.assertEquals(1, len(urls))
        self.assertEquals(fu + '/f1/p1', urls[0])

    def test_search_ignore_ids(self):
        self.folder.invokeFactory('Folder', 'f1')
        self.folder.invokeFactory('Folder', 'f2')
        self.folder.f1.invokeFactory('Document', 'p1')
        self.folder.f1.invokeFactory('Document', 'p2')
        self.folder.f1.invokeFactory('Document', 'p3', title='view')
        fu = self.folder.absolute_url()
        view = self.view(self.portal, fu + '/f2/p1/view')
        urls = sorted([b.getURL() for b in view.search_for_similar()])
        self.assertEquals(1, len(urls))
        self.assertEquals(fu + '/f1/p1', urls[0])

    def test_search_node(self):
        self.folder.invokeFactory('Folder', 'f1')
        self.folder.invokeFactory('Folder', 'f2')
        self.folder.f1.invokeFactory('Document', 'p1')
        self.folder.f1.invokeFactory('Document', 'p2')
        fu = self.folder.absolute_url()
        view = self.view(self.portal, fu + '/f2/p1/f3')
        urls = sorted([b.getURL() for b in view.search_for_similar()])
        self.assertEquals(1, len(urls))
        self.assertEquals(fu + '/f1/p1', urls[0])

    def test_search_parens(self):
        self.folder.invokeFactory('Folder', 'f1')
        self.folder.invokeFactory('Folder', 'f2')
        self.folder.f1.invokeFactory('Document', 'p1')
        self.folder.f1.invokeFactory('Document', 'p2')
        fu = self.folder.absolute_url()
        view = self.view(self.portal, fu + '/f2/p1/f3(')
        urls = sorted([b.getURL() for b in view.search_for_similar()])
        self.assertEquals(1, len(urls))
        self.assertEquals(fu + '/f1/p1', urls[0])
    
    def test_search_query_parser_error(self):
        view = self.view(self.portal, self.portal.absolute_url() + '/&')
        try:
            urls = view.search_for_similar()
        except:
            self.fail('Query parsing error was not handled.')

    def test_search_blacklisted(self):
        self.folder.invokeFactory('Folder', 'f1')
        self.folder.invokeFactory('Folder', 'f2')
        self.folder.f1.invokeFactory('Document', 'p1')
        self.folder.f1.invokeFactory('Document', 'p2')
        fu = self.folder.absolute_url()
        self.portal.portal_properties.site_properties.types_not_searched = ['Document']
        view = self.view(self.portal, fu + '/f2/p1')
        urls = sorted([b.getURL() for b in view.search_for_similar()])
        self.assertEquals(1, len(urls))
        self.assertEquals(fu + '/f2', urls[0])


def test_suite():
    suite = unittest.TestSuite()
    suite.addTest(unittest.makeSuite(TestRedirectorView))
    return suite
