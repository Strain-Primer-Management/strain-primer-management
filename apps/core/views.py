from django.views.generic import TemplateView


class HomeView(TemplateView):
    """PLACEHOLDER landing page. Login is enforced globally by LoginRequiredMiddleware."""

    template_name = "core/home.html"
