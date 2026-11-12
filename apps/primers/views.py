from django.views.generic import TemplateView


class IndexView(TemplateView):
    """PLACEHOLDER so the page and navigation exist from day one.

    Replace with the real list view in the Jira ticket for primers. Context contract for the
    frontend: document every variable you pass to the template in the view's docstring.
    """

    template_name = "primers/index.html"
