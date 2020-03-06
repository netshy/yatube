import time

from django.core.cache.utils import make_template_fragment_key
from django.test import TestCase, Client, override_settings
from django.core import mail
from django.core.cache import cache

from yatube.settings import TEST_CACHE
from .models import User, Post, Group, Follow
from .forms import PostForm


@override_settings(CACHES=TEST_CACHE)
class ProfileTest(TestCase):
    def setUp(self):  # Не забудь создать 2 файла: 1 картинка, другая не картинка (.txt)
        self.client = Client()
        self.user = User.objects.create_user(username='test_user', email='example@ex.com', password='skynetMy')
        self.user2 = User.objects.create_user(username='test_user2', email='example2@ex.com', password='skynetMy')
        self.user3 = User.objects.create_user(username='test_user3', email='example3@ex.com', password='skynetMy')
        self.group = Group.objects.create(title='Cats', slug='cats', description='Описание группы', rules='Правила')
        self.post = Post.objects.create(group=self.group, text='Я могу создать пост', image='posts/author.jpg/',
                                        author=self.user)
        self.client.post('/auth/login/', data={'username': 'test_user', 'password': 'skynetMy'}, follow=True)

    def test_send_mail_registration(self):
        self.client.post('/auth/signup/',
                         data={
                             'username': 'test_user_mail',
                             'email': 'example@ex.com',
                             'password': 'skynetMy',
                             'password1': 'skynetMy',
                             'password2': 'skynetMy',
                         }, follow=True)
        self.assertEqual(len(mail.outbox), 1, msg='Письмо не отправлено')
        self.assertEqual(mail.outbox[0].subject, 'Подтверждение регистрации Yatube', msg='Тема письма неверная')

    def test_create_user_profile(self):
        response = self.client.get('/{username}/'.format(username='test_user'))
        self.assertEqual(response.status_code, 200)

    def test_create_post_authorized_user(self):
        response = self.client.post('/new/', data={'group': 1, 'text': 'Другой пост тоже создается'}, follow=True)
        self.assertRedirects(response, '/', status_code=302, target_status_code=200)
        self.assertContains(response, text='Другой пост тоже создается', count=1, msg_prefix='Пост не найден')

    def test_redirect_create_post_unauthorized_user(self):
        self.client.logout()
        response = self.client.get('/new/')
        self.assertRedirects(response, '/auth/login/?next=/new/', status_code=302, target_status_code=200)

    def test_pulished_post(self):
        response1 = self.client.get('/')
        response2 = self.client.get('/{username}/'.format(username='test_user'))
        response3 = self.client.get('/{username}/{post_id}/'.format(username='test_user', post_id=self.post.id),
                                    follow=True)

        self.assertContains(response1, text='Я могу создать пост', count=1, msg_prefix='Нет поста на главной странице')
        self.assertContains(response2, text='Я могу создать пост', count=1, msg_prefix='Нет поста на странице профиля')
        self.assertContains(response3, text='Я могу создать пост', count=1, msg_prefix='Нет поста на странице поста')

    def test_authorized_user_can_edit(self):
        response_edit_post = self.client.post(
            path='/{username}/{post_id}/edit/'.format(username='test_user', post_id=self.post.id),
            data={'text': 'Изменили текст поста'}, follow=True)

        response1 = self.client.get('/')
        response2 = self.client.get('/{username}/'.format(username='test_user'))
        response3 = self.client.get('/{username}/{post_id}/'.format(username='test_user', post_id=self.post.id),
                                    follow=True)

        self.assertRedirects(response_edit_post,
                             expected_url='/{username}/{post_id}/'.format(username='test_user', post_id=self.post.id),
                             status_code=302, target_status_code=200, msg_prefix='Проверь путь запроса')

        self.assertContains(response1, text='Изменили текст поста', count=1,
                            msg_prefix='Пост не изменился на главной странице')
        self.assertContains(response2, text='Изменили текст поста', count=1,
                            msg_prefix='Пост не изменился на странице профиля')
        self.assertContains(response3, text='Изменили текст поста', count=1,
                            msg_prefix='Пост не изменился на странице поста')

    def test_post_image(self):
        response = self.client.get('/{username}/{post_id}/'.format(username='test_user', post_id=self.post.id),
                                   follow=True)
        self.assertContains(response, text='<img', status_code=200, msg_prefix='Картинки нет')

    def test_post_index_image(self):
        response = self.client.get('/')
        self.assertContains(response, text='<img', status_code=200, msg_prefix='Картинки нет')

    def test_post_profile_image(self):
        response = self.client.get('/{username}/'.format(username='test_user'))
        self.assertContains(response, text='<img', status_code=200, msg_prefix='Картинки нет')

    def test_image_form_file_upload(self):  # Вставь сюда существующий файл (не картинку)
        with open('requirements.txt', 'rb') as fp:
            form_data = {'author': self.user, 'text': 'Любой текст', 'group': self.group, 'image': fp}
            form = PostForm(data=form_data)
            self.assertFalse(form.is_valid(), msg='Форма не валидна')

            response = self.client.post(path='/{username}/{post_id}/edit/'.format(username='test_user',
                                                                                  post_id=self.post.id), data=form_data)
            self.assertFormError(response, 'form', 'image', errors=(
                'Загрузите правильное изображение. '
                'Файл, который вы загрузили, поврежден '
                'или не является изображением.'
            ), msg_prefix='Форма через сайт не валидна')

    def test_authorized_user_can_following_and_delete_followers(self):
        response_follow_1 = self.client.get('/test_user2/follow/', follow=True)
        response_follow_2 = self.client.get('/test_user3/follow/', follow=True)

        self.assertRedirects(response_follow_1, expected_url='/test_user2/', status_code=302, target_status_code=200,
                             msg_prefix='Не смог подписаться на пользователя "test_user2"')

        self.assertRedirects(response_follow_2, expected_url='/test_user3/', status_code=302, target_status_code=200,
                             msg_prefix='Не смог подписаться на пользователя "test_user3"')

        self.assertNotContains(response_follow_1, text='Подписаться', msg_prefix='Нет кнопки "Подписаться" test_user2')
        self.assertNotContains(response_follow_2, text='Подписаться', msg_prefix='Нет кнопки "Подписаться" test_user3')
        self.assertContains(response_follow_1, text='Отписаться', msg_prefix='Нет кнопки "Отписаться" test_user2')
        self.assertContains(response_follow_2, text='Отписаться', msg_prefix='Нет кнопки "Отписаться" test_user3')

        response_unfollow_1 = self.client.get('/test_user2/unfollow/', follow=True)
        response_unfollow_2 = self.client.get('/test_user3/unfollow/', follow=True)

        self.client.get('/test_user3/follow/')
        self.assertEqual(Follow.objects.filter(author=self.user3).count(), second=1,
                         msg='В БД не отразилась подписка на test_user3')
        self.client.get('/test_user2/follow/')
        self.assertEqual(Follow.objects.filter(author=self.user2).count(), second=1,
                         msg='В БД не отразилась подписка на test_user2')

        self.assertRedirects(response_unfollow_1, expected_url='/test_user2/', status_code=302, target_status_code=200,
                             msg_prefix='Не смог отписаться "test_user2"')
        self.assertRedirects(response_unfollow_2, expected_url='/test_user3/', status_code=302, target_status_code=200,
                             msg_prefix='Не смог отписаться на пользователя "test_user3"')

        self.assertContains(response_unfollow_1, text='Подписаться', msg_prefix='Нет кнопки "Подписаться" test_user2')
        self.assertContains(response_unfollow_2, text='Подписаться', msg_prefix='Нет кнопки "Подписаться" test_user3')
        self.assertNotContains(response_unfollow_1, text='Отписаться', msg_prefix='Нет кнопки "Отписаться" test_user2')
        self.assertNotContains(response_unfollow_2, text='Отписаться', msg_prefix='Нет кнопки "Отписаться" test_user3')

    def test_new_post_in_follow_authors_and_not_visible_post_unfollowed_authors(self):
        Post.objects.create(group=self.group, text='Я найду этот текст', image='posts/author.jpg/',
                            author=self.user2)
        Post.objects.create(group=self.group, text='К сожалению, не суждено быть любимым', image='posts/author.jpg/',
                            author=self.user3)

        response_follow = self.client.get('/test_user2/follow/', follow=True)
        response_follow_favorite = self.client.get('/follow/')
        self.assertEqual(response_follow_favorite.status_code, 200, msg='Нет доступа к странице избранных авторов')

        self.assertRedirects(response_follow, expected_url='/test_user2/', status_code=302, target_status_code=200,
                             msg_prefix='Не смог подписаться на пользователя "test_user2"')

        self.assertContains(response_follow_favorite, text='Я найду этот текст', count=1,
                            msg_prefix='Пост не найден в избранных авторах')
        self.assertNotContains(response_follow_favorite, text='К сожалению, не суждено быть любимым',
                               msg_prefix='Этого текста не должно быть')

    def test_only_authorized_user_can_comment(self):
        response = self.client.post('/{username}/{post_id}/comment/'.format(username='test_user', post_id=self.post.id),
                                    data={'text': 'Комментарий!'}, follow=True)
        self.assertContains(response, text='Комментарий!', count=1, msg_prefix='Комментарий не найден')

        self.client.logout()

        response2 = self.client.post('/{username}/{post_id}/comment/'.format(username='test_user', post_id=self.post.id),
                                     data={'text': 'Комментарий!'}, follow=True)
        self.assertNotContains(response2, text='Комментарий!', msg_prefix='Комментария быть не должно')


class ServerErrorsTest(TestCase):
    def test_404_page_not_found(self):
        response = self.client.get('/page_never_be_real/')
        self.assertEqual(response.status_code, 404, msg='Проверь существование страницы')


class Cache(TestCase):
    def setUp(self):
        User.objects.create_user(username='test_user', email='example@ex.com', password='skynetMy')
        self.client.post('/auth/login/', data={'username': 'test_user', 'password': 'skynetMy'}, follow=False)

    def test_cache(self):
        key = make_template_fragment_key('index_page', [1])
        self.assertFalse(cache.get(key))
        self.client.get("/")
        self.assertTrue(cache.get(key))

    def test_cache_index(self):
        response = self.client.post('/new/', data={'text': 'Проверка кэша'}, follow=True)
        response1 = self.client.get('/')

        self.assertRedirects(response, '/', status_code=302, target_status_code=200)
        self.assertNotContains(response1, text='Проверка кэша', msg_prefix='Поста не должно быть на странице')

        cache.clear()
        self.assertContains(response=self.client.get('/'), text='Проверка кэша', count=1,
                            msg_prefix='После очистки кэша не видно пост')
