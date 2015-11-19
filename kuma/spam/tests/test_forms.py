from django import forms
from django.test import SimpleTestCase, RequestFactory
from django.utils import six
from django.utils.encoding import force_unicode

from constance.test.utils import override_config
from nose.plugins.attrib import attr
from waffle.models import Flag
import responses

from ..constants import CHECK_URL_RE, SPAM_CHECKS_FLAG, VERIFY_URL_RE
from ..forms import AkismetCheckFormMixin


class AkismetCheckTestForm(AkismetCheckFormMixin, forms.Form):

    def akismet_parameters(self):
        parameters = {
            'blog_lang': 'en_us',
            'blog_charset': 'UTF-8',
            'comment_author': 'testuser',
            'comment_author_email': 'testuser@test.com',
            'comment_type': 'wiki-revision',
            'user_ip': '0.0.0.0',
            'user_agent': 'Mozilla Firefox',
            'referrer': 'https://www.netscape.com/',
        }
        parameters.update(self.cleaned_data)
        return parameters


class AkismetContentTestForm(AkismetCheckTestForm):
    content = forms.CharField()


@attr('spam')
class AkismetFormTests(SimpleTestCase):
    rf = RequestFactory()
    remote_addr = '0.0.0.0'
    http_user_agent = 'Mozilla Firefox'
    http_referer = 'https://www.netscape.com/'

    def setUp(self):
        super(AkismetFormTests, self).setUp()
        responses.start()
        self.request = self.rf.get(
            '/',
            REMOTE_ADDR=self.remote_addr,
            HTTP_USER_AGENT=self.http_user_agent,
            HTTP_REFERER=self.http_referer,
        )
        Flag.objects.update_or_create(
            name=SPAM_CHECKS_FLAG,
            defaults={'everyone': True},
        )

    def tearDown(self):
        super(AkismetFormTests, self).tearDown()
        responses.stop()
        responses.reset()
        Flag.objects.update_or_create(
            name=SPAM_CHECKS_FLAG,
            defaults={'everyone': None},
        )

    @override_config(AKISMET_KEY='parameters')
    def test_akismet_parameters(self):
        responses.add(responses.POST, VERIFY_URL_RE, body='valid')
        responses.add(responses.POST, CHECK_URL_RE, body='true')

        form = AkismetContentTestForm(
            self.request,
            data={'content': 'some content'},
        )
        six.assertRaisesRegex(
            self,
            AttributeError,
            "'AkismetContentTestForm' object has no attribute 'cleaned_data'",
            form.akismet_parameters,
        )
        self.assertTrue(form.is_valid())
        self.assertIn('content', form.cleaned_data)
        parameters = form.akismet_parameters()
        self.assertEqual(parameters['content'], 'some content')
        # super method called
        self.assertEqual(parameters['user_ip'], self.remote_addr)
        self.assertEqual(parameters['user_agent'], self.http_user_agent)
        self.assertEqual(parameters['referrer'], self.http_referer)

    @override_config(AKISMET_KEY='enabled')
    def test_akismet_enabled(self):
        responses.add(responses.POST, VERIFY_URL_RE, body='valid')
        responses.add(responses.POST, CHECK_URL_RE, body='true')
        form = AkismetCheckTestForm(self.request, data={})
        self.assertTrue(form.akismet_enabled())

    @override_config(AKISMET_KEY='')
    def test_akismet_not_enabled(self):
        responses.add(responses.POST, VERIFY_URL_RE, body='valid')
        responses.add(responses.POST, CHECK_URL_RE, body='true')
        form = AkismetCheckTestForm(self.request, data={})
        self.assertFalse(form.akismet_enabled())

    @override_config(AKISMET_KEY='error')
    def test_akismet_error(self):
        responses.add(responses.POST, VERIFY_URL_RE, body='valid')
        responses.add(responses.POST, CHECK_URL_RE, body='yada yada')

        form = AkismetCheckTestForm(self.request, data={})
        # not valid because we found a wrong response from akismet
        self.assertFalse(form.is_valid())
        self.assertIn(form.akismet_error_message, form.errors['__all__'])
        six.assertRaisesRegex(
            self,
            forms.ValidationError,
            force_unicode(form.akismet_error_message),
            form.akismet_error,
        )

    @override_config(AKISMET_KEY='clean')
    def test_form_clean(self):
        responses.add(responses.POST, VERIFY_URL_RE, body='valid')
        responses.add(responses.POST, CHECK_URL_RE, body='true')

        form = AkismetCheckTestForm(self.request, data={})
        self.assertTrue(form.is_valid())
        self.assertEqual(form.errors, {})
