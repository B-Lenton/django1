import datetime

from django.test import TestCase
from django.utils import timezone
from django.urls import reverse
from unittest import skip

from .models import Question, Choice


class QuestionModelTests(TestCase):

    def test_was_published_recently_with_future_question(self):
        """
        was_published_recently() returns False for questions whose pub_date
        is in the future.
        """
        time = timezone.now() + datetime.timedelta(days=30)
        future_question = Question(pub_date=time)
        self.assertIs(future_question.was_published_recently(), False)

    def test_was_published_recently_with_old_question(self):
        """
        was_published_recently() returns False for questions whose pub_date
        is older than 1 day.
        """
        time = timezone.now() - datetime.timedelta(days=1, seconds=1)
        old_question = Question(pub_date=time)
        self.assertIs(old_question.was_published_recently(), False)

    def test_was_published_recently_with_recent_question(self):
        """
        was_published_recently() returns True for questions whose pub_date
        is within the last day.
        """
        time = timezone.now() - datetime.timedelta(hours=23, minutes=59, seconds=59)
        recent_question = Question(pub_date=time)
        self.assertIs(recent_question.was_published_recently(), True)


def create_question(question_text, days, choices):
    """
    Create a question with the given `question_text` and published the
    given number of `days` offset to now (negative for questions published
    in the past, positive for questions that have yet to be published).
    """
    assert isinstance(choices, list)  # choices must be a list of strings
    time = timezone.now() + datetime.timedelta(days=days)
    question = Question.objects.create(question_text=question_text, pub_date=time)
    for choice in choices:
        Choice.objects.create(question=question, choice_text=choice)  # populate question with empty choices list
    return question


class QuestionIndexViewTests(TestCase):
    def test_no_questions(self):
        """
        If no questions exist, an appropriate message is displayed.
        """
        response = self.client.get(reverse('polls:index'))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "No polls are available.")
        self.assertQuerysetEqual(response.context['latest_question_list'], [])

    def test_past_question(self):
        """
        Questions with a pub_date in the past are displayed on the index page.
        """
        question = create_question(question_text='Past question.', days=-30, choices=['past choice'])
        response = self.client.get(reverse('polls:index'))
        self.assertQuerysetEqual(response.context['latest_question_list'], [question])

    def test_future_question(self):
        """
        Questions with a pub_date in the future aren't displayed on the index page.
        """
        question = create_question(question_text="Future question.", days=30, choices=['future choice'])
        response = self.client.get(reverse('polls:index'))
        self.assertContains(response, "No polls are available.")
        self.assertQuerysetEqual(response.context['latest_question_list'], [])

    def test_future_question_and_past_question(self):
        """
        Even if both past and future questions exist, only past questions
        are displayed.
        """
        question_past = create_question(question_text="Past question.", days=-30, choices=['past choice'])
        question_future = create_question(question_text="Future question.", days=30, choices=['future choice'])
        response = self.client.get(reverse('polls:index'))
        question_count = Question.objects.count()
        self.assertEqual(question_count, 2)
        self.assertQuerysetEqual(
            response.context['latest_question_list'],
            [question_past],
        )

    def test_two_past_questions(self):
        """
        The questions index page may display multiple questions.
        """
        question1 = create_question(question_text="Past question 1.", days=-5, choices=['past choice 1'])
        question2 = create_question(question_text="Past question 2.", days=-30, choices=['past choice 2'])
        response = self.client.get(reverse('polls:index'))
        self.assertQuerysetEqual(
            response.context['latest_question_list'],
            [question1, question2],
        )

    def test_empty_question(self):
        """
        Questions with no choices are not displayed on the index page.
        """
        empty_question = create_question(question_text="No choices.", days=-5, choices=[])
        response = self.client.get(reverse('polls:index'))
        self.assertQuerysetEqual(
            response.context['latest_question_list'], []
        )


class QuestionDetailViewTests(TestCase):
    def test_future_question(self):
        """
        The detail view of a question with a pub_date in the future
        returns a 404 not found.
        """
        future_question = create_question(question_text='Future question.', days=5, choices=['future choice'])
        url = reverse('polls:detail', args=(future_question.id,))
        response = self.client.get(url)
        self.assertEqual(response.status_code, 404)

    def test_past_question(self):
        """
        The detail view of a question with a pub_date in the past
        displays the question's text.
        """
        past_question = create_question(question_text='Past question.', days=-5, choices=['past choice'])
        url = reverse('polls:detail', args=(past_question.id,))
        response = self.client.get(url)
        self.assertContains(response, past_question.question_text)

    def test_empty_question(self):
        """
        The detail view of a question with no Choices
        returns a 404 not found.
        """
        empty_question = create_question(question_text="No choices.", days=-5, choices=[])
        url = reverse('polls:detail', args=(empty_question.id,))
        response = self.client.get(url)
        self.assertEqual(response.status_code, 404)


class QuestionResultsViewTests(TestCase):
    def test_future_question(self):
        """
        The results page of a question with a pub_date in the future returns a 404 not found.
        """
        future_question = create_question(question_text='Future question.', days=5, choices=['future choice'])
        url = reverse('polls:results', args=(future_question.id,))
        response = self.client.get(url)
        self.assertEqual(response.status_code, 404)

    def test_past_question(self):
        """
        The results page of a question with a pub_date in the past displays the results of the votes.
        """
        past_question = create_question(question_text='Past question.', days=-5, choices=['past choice'])
        url = reverse('polls:results', args=(past_question.id,))
        response = self.client.get(url)
        self.assertContains(response, past_question.question_text)

    def test_empty_question(self):
        """
        The results page of a question with no Choices
        returns a 404 not found.
        """
        empty_question = create_question(question_text="No choices.", days=-5, choices=[])
        url = reverse('polls:results', args=(empty_question.id,))
        response = self.client.get(url)
        self.assertEqual(response.status_code, 404)
